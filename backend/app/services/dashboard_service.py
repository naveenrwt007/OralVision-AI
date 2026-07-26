from datetime import datetime, timedelta, timezone

from app.core.database import (
    patients_collection,
    reports_collection,
    screenings_collection,
)
from app.models.patient import serialize_patients


SUSPICIOUS_LABELS = [
    "CANCER",
    "SUSPICIOUS",
    "PRECANCER",
    "PRE_CANCER",
    "PRE-CANCER",
]

NON_CANCER_LABELS = [
    "NON_CANCER",
    "NON CANCER",
    "NON-CANCER",
    "NORMAL",
]

POOR_QUALITY_LABELS = [
    "poor",
    "rejected",
    "unacceptable",
    "low",
    "warning",
]


def _month_start(value: datetime) -> datetime:
    return value.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _shift_month(value: datetime, months: int) -> datetime:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero_based = divmod(month_index, 12)

    return value.replace(
        year=year,
        month=month_zero_based + 1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _complete_month_series(
    raw_results: list[dict],
    value_key: str,
    months: int = 12,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    first_month = _shift_month(_month_start(now), -(months - 1))

    values_by_month = {
        str(item.get("_id")): int(item.get("count", 0))
        for item in raw_results
        if item.get("_id")
    }

    series = []

    for offset in range(months):
        month_date = _shift_month(first_month, offset)
        month_key = month_date.strftime("%Y-%m")

        series.append(
            {
                "month": month_date.strftime("%b %Y"),
                "month_key": month_key,
                value_key: values_by_month.get(month_key, 0),
            }
        )

    return series


async def _monthly_counts(
    collection,
    value_key: str,
    date_expression,
    months: int = 12,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    first_month = _shift_month(_month_start(now), -(months - 1))

    pipeline = [
        {
            "$project": {
                "analytics_date": date_expression,
            }
        },
        {
            "$match": {
                "analytics_date": {
                    "$type": "date",
                    "$gte": first_month,
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$analytics_date",
                        "timezone": "UTC",
                    }
                },
                "count": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "_id": 1,
            }
        },
    ]

    results = await collection.aggregate(
        pipeline
    ).to_list(length=months + 2)

    return _complete_month_series(
        results,
        value_key=value_key,
        months=months,
    )


async def get_dashboard_statistics() -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    tomorrow_start = today_start + timedelta(days=1)
    seven_days_ago = now - timedelta(days=7)

    total_patients = await patients_collection.count_documents({})
    total_screenings = await screenings_collection.count_documents({})
    total_reports = await reports_collection.count_documents({})

    # Exact matching prevents NON_CANCER from being counted as CANCER.
    suspicious_cases = await screenings_collection.count_documents(
        {
            "prediction": {
                "$in": SUSPICIOUS_LABELS,
            }
        }
    )

    non_cancer_cases = await screenings_collection.count_documents(
        {
            "prediction": {
                "$in": NON_CANCER_LABELS,
            }
        }
    )

    today_reports = await reports_collection.count_documents(
        {
            "$or": [
                {
                    "created_at": {
                        "$gte": today_start,
                        "$lt": tomorrow_start,
                    }
                },
                {
                    "generated_at": {
                        "$gte": today_start,
                        "$lt": tomorrow_start,
                    },
                    "created_at": {
                        "$exists": False,
                    },
                },
            ]
        }
    )

    recent_screenings = await screenings_collection.count_documents(
        {
            "created_at": {
                "$gte": seven_days_ago,
            }
        }
    )

    recent_reports = await reports_collection.count_documents(
        {
            "$or": [
                {
                    "created_at": {
                        "$gte": seven_days_ago,
                    }
                },
                {
                    "generated_at": {
                        "$gte": seven_days_ago,
                    },
                    "created_at": {
                        "$exists": False,
                    },
                },
            ]
        }
    )

    confidence_pipeline = [
        {
            "$project": {
                "confidence_value": {
                    "$cond": [
                        {
                            "$ne": [
                                {
                                    "$ifNull": [
                                        "$confidence_percent",
                                        None,
                                    ]
                                },
                                None,
                            ]
                        },
                        {
                            "$convert": {
                                "input": "$confidence_percent",
                                "to": "double",
                                "onError": None,
                                "onNull": None,
                            }
                        },
                        {
                            "$multiply": [
                                {
                                    "$convert": {
                                        "input": "$confidence",
                                        "to": "double",
                                        "onError": None,
                                        "onNull": None,
                                    }
                                },
                                100,
                            ]
                        },
                    ]
                }
            }
        },
        {
            "$match": {
                "confidence_value": {
                    "$ne": None,
                    "$gte": 0,
                    "$lte": 100,
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "average": {
                    "$avg": "$confidence_value",
                },
            }
        },
    ]

    confidence_results = await screenings_collection.aggregate(
        confidence_pipeline
    ).to_list(length=1)

    average_confidence = (
        round(float(confidence_results[0]["average"]), 2)
        if confidence_results
        and confidence_results[0].get("average") is not None
        else 0.0
    )

    quality_status_expression = {
        "$toLower": {
            "$convert": {
                "input": {
                    "$ifNull": [
                        "$image_quality.status",
                        {
                            "$ifNull": [
                                "$image_quality_status",
                                "unknown",
                            ]
                        },
                    ]
                },
                "to": "string",
                "onError": "unknown",
                "onNull": "unknown",
            }
        }
    }

    poor_quality_images = await screenings_collection.count_documents(
        {
            "$expr": {
                "$in": [
                    quality_status_expression,
                    POOR_QUALITY_LABELS,
                ]
            }
        }
    )

    quality_pipeline = [
        {
            "$group": {
                "_id": quality_status_expression,
                "count": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "count": -1,
            }
        },
    ]

    quality_results = await screenings_collection.aggregate(
        quality_pipeline
    ).to_list(length=20)

    quality_distribution = {
        str(item.get("_id") or "unknown"): int(item.get("count", 0))
        for item in quality_results
    }

    gender_pipeline = [
        {
            "$group": {
                "_id": {
                    "$toLower": {
                        "$convert": {
                            "input": {
                                "$ifNull": [
                                    "$gender",
                                    "unknown",
                                ]
                            },
                            "to": "string",
                            "onError": "unknown",
                            "onNull": "unknown",
                        }
                    }
                },
                "count": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "count": -1,
            }
        },
    ]

    gender_results = await patients_collection.aggregate(
        gender_pipeline
    ).to_list(length=20)

    gender_distribution = {
        str(item.get("_id") or "unknown"): int(item.get("count", 0))
        for item in gender_results
    }

    monthly_screenings = await _monthly_counts(
        screenings_collection,
        value_key="screenings",
        date_expression="$created_at",
    )

    monthly_reports = await _monthly_counts(
        reports_collection,
        value_key="reports",
        date_expression={
            "$ifNull": [
                "$created_at",
                "$generated_at",
            ]
        },
    )

    confidence_trend_pipeline = [
        {
            "$project": {
                "created_at": 1,
                "confidence_value": {
                    "$cond": [
                        {
                            "$ne": [
                                {
                                    "$ifNull": [
                                        "$confidence_percent",
                                        None,
                                    ]
                                },
                                None,
                            ]
                        },
                        {
                            "$convert": {
                                "input": "$confidence_percent",
                                "to": "double",
                                "onError": None,
                                "onNull": None,
                            }
                        },
                        {
                            "$multiply": [
                                {
                                    "$convert": {
                                        "input": "$confidence",
                                        "to": "double",
                                        "onError": None,
                                        "onNull": None,
                                    }
                                },
                                100,
                            ]
                        },
                    ]
                },
            }
        },
        {
            "$match": {
                "created_at": {
                    "$type": "date",
                    "$gte": _shift_month(
                        _month_start(now),
                        -11,
                    ),
                },
                "confidence_value": {
                    "$ne": None,
                    "$gte": 0,
                    "$lte": 100,
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$created_at",
                        "timezone": "UTC",
                    }
                },
                "average_confidence": {
                    "$avg": "$confidence_value",
                },
            }
        },
        {
            "$sort": {
                "_id": 1,
            }
        },
    ]

    confidence_trend_results = await screenings_collection.aggregate(
        confidence_trend_pipeline
    ).to_list(length=14)

    confidence_by_month = {
        str(item["_id"]): round(
            float(item.get("average_confidence", 0)),
            2,
        )
        for item in confidence_trend_results
        if item.get("_id")
    }

    confidence_trend = [
        {
            "month": item["month"],
            "month_key": item["month_key"],
            "average_confidence": confidence_by_month.get(
                item["month_key"],
                0.0,
            ),
        }
        for item in monthly_screenings
    ]

    recent_patient_cursor = (
        patients_collection
        .find({})
        .sort("created_at", -1)
        .limit(5)
    )

    recent_patients = await recent_patient_cursor.to_list(
        length=5
    )

    return {
        "summary": {
            "total_patients": total_patients,
            "total_screenings": total_screenings,
            "total_reports": total_reports,
            "suspicious_cases": suspicious_cases,
            "cancer_cases": suspicious_cases,
            "non_cancer_cases": non_cancer_cases,
            "today_reports": today_reports,
            "average_confidence": average_confidence,
            "poor_quality_images": poor_quality_images,
        },
        "last_7_days": {
            "screenings": recent_screenings,
            "reports": recent_reports,
        },
        "outcome_distribution": {
            "suspicious": suspicious_cases,
            "non_cancer": non_cancer_cases,
        },
        "monthly_screenings": monthly_screenings,
        "monthly_reports": monthly_reports,
        "confidence_trend": confidence_trend,
        "quality_distribution": quality_distribution,
        "gender_distribution": gender_distribution,
        "recent_patients": serialize_patients(
            recent_patients
        ),
        "generated_at": now.isoformat(),
    }