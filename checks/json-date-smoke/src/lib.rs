//! Offline consumption checks for Flax's JSON and date dependencies.

#[cfg(test)]
mod tests {
    use chrono::{DateTime, NaiveDate};
    use serde::{Deserialize, Serialize};
    use serde_json::{json, Value};

    #[derive(Deserialize)]
    struct DailyResponse {
        rt_cd: String,
        output1: Symbol,
        output2: Vec<DailyStrings>,
    }

    #[derive(Deserialize)]
    struct Symbol {
        stck_shrn_iscd: String,
    }

    #[derive(Deserialize)]
    struct DailyStrings {
        stck_bsop_date: String,
        stck_oprc: String,
        stck_hgpr: String,
        stck_lwpr: String,
        stck_clpr: String,
        acml_vol: String,
        acml_tr_pbmn: String,
    }

    #[derive(Deserialize)]
    struct Manifest {
        symbol: String,
        requested_start: String,
        requested_end: String,
        samples: Vec<Sample>,
    }

    #[derive(Deserialize)]
    struct Sample {
        file: String,
        retrieved_at: String,
    }

    #[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
    struct ResultRecord {
        source_ref: String,
        symbol: String,
        received_at_micros: i64,
    }

    #[test]
    fn daily_json_bytes_preserve_date_and_exact_integer_fields() {
        let original = include_bytes!("../fixtures/daily.json");
        let response: DailyResponse = serde_json::from_slice(original).unwrap();

        assert_eq!(response.rt_cd, "0");
        assert_eq!(response.output1.stck_shrn_iscd, "005930");
        assert_eq!(response.output2.len(), 1);
        let row = &response.output2[0];
        let date = NaiveDate::parse_from_str(&row.stck_bsop_date, "%Y%m%d").unwrap();
        assert_eq!(date, NaiveDate::from_ymd_opt(2026, 10, 1).unwrap());
        for (text, expected) in [
            (&row.stck_oprc, 266_500_u64),
            (&row.stck_hgpr, 276_000),
            (&row.stck_lwpr, 264_500),
            (&row.stck_clpr, 276_000),
            (&row.acml_vol, 13_741_073),
            (&row.acml_tr_pbmn, 3_726_945_890_883),
        ] {
            assert_eq!(text.parse::<u64>().unwrap(), expected);
        }
    }

    #[test]
    fn integers_beyond_float_precision_roundtrip_as_exact_json_numbers() {
        for (text, expected) in [
            ("9007199254740993", 9_007_199_254_740_993_u64),
            ("18446744073709551615", u64::MAX),
        ] {
            let input = format!(r#"{{"value":"{text}"}}"#);
            let original: Value = serde_json::from_slice(input.as_bytes()).unwrap();
            let value = original["value"].as_str().unwrap().parse::<u64>().unwrap();
            assert_eq!(value, expected);

            let output = serde_json::to_vec(&json!({"value": value})).unwrap();
            let decoded: Value = serde_json::from_slice(&output).unwrap();
            assert_eq!(decoded["value"].as_u64(), Some(expected));
            assert_eq!(
                String::from_utf8(output).unwrap(),
                format!(r#"{{"value":{text}}}"#)
            );
        }
    }

    #[test]
    fn out_of_range_and_invalid_integer_strings_are_rejected() {
        for text in ["18446744073709551616", "-1", "1.5", ""] {
            assert!(text.parse::<u64>().is_err(), "accepted {text:?}");
        }
    }

    #[test]
    fn manifest_and_jsonl_records_roundtrip_with_collection_time() {
        let manifest: Manifest =
            serde_json::from_slice(include_bytes!("../fixtures/manifest.json")).unwrap();
        assert_eq!(manifest.symbol, "005930");
        for text in [&manifest.requested_start, &manifest.requested_end] {
            NaiveDate::parse_from_str(text, "%Y-%m-%d").unwrap();
        }
        assert_eq!(manifest.samples.len(), 1);
        let sample = &manifest.samples[0];
        assert_eq!(sample.file, "daily-raw-01.json");
        let record = ResultRecord {
            source_ref: sample.file.clone(),
            symbol: manifest.symbol,
            received_at_micros: DateTime::parse_from_rfc3339(&sample.retrieved_at)
                .unwrap()
                .timestamp_micros(),
        };
        assert_eq!(record.received_at_micros, 1_790_899_775_581_009);

        let single_json = serde_json::to_string(&record).unwrap();
        assert_eq!(
            serde_json::from_str::<ResultRecord>(&single_json).unwrap(),
            record
        );
        let mut jsonl = Vec::new();
        for _ in 0..2 {
            serde_json::to_writer(&mut jsonl, &record).unwrap();
            jsonl.push(b'\n');
        }
        let text = String::from_utf8(jsonl).unwrap();
        assert_eq!(text.lines().count(), 2);
        for line in text.lines() {
            assert_eq!(serde_json::from_str::<ResultRecord>(line).unwrap(), record);
        }
    }

    #[test]
    fn explicit_offset_and_utc_times_produce_identical_microseconds() {
        let offset = DateTime::parse_from_rfc3339("2026-10-02T09:09:35.581009+09:00")
            .unwrap()
            .timestamp_micros();
        let utc = DateTime::parse_from_rfc3339("2026-10-02T00:09:35.581009Z")
            .unwrap()
            .timestamp_micros();
        assert_eq!(offset, 1_790_899_775_581_009);
        assert_eq!(utc, offset);
    }

    #[test]
    fn calendar_formats_agree_and_validate_leap_days() {
        let compact = NaiveDate::parse_from_str("20261001", "%Y%m%d").unwrap();
        let dashed = NaiveDate::parse_from_str("2026-10-01", "%Y-%m-%d").unwrap();
        assert_eq!(compact, dashed);
        assert_eq!(
            NaiveDate::parse_from_str("20240229", "%Y%m%d").unwrap(),
            NaiveDate::from_ymd_opt(2024, 2, 29).unwrap()
        );
        for text in ["20230229", "20261301", "20260431"] {
            assert!(NaiveDate::parse_from_str(text, "%Y%m%d").is_err());
        }
    }

    #[test]
    fn malformed_json_and_rfc3339_are_rejected() {
        assert!(serde_json::from_slice::<Value>(br#"{"output2":["#).is_err());
        for text in [
            "not a timestamp",
            "2026-02-30T00:00:00Z",
            "2026-10-02T00:09:35.581009",
        ] {
            assert!(DateTime::parse_from_rfc3339(text).is_err());
        }
    }
}
