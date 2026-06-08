import argparse
import pandas as pd
import numpy as np
import yaml
import json
import logging
import time


def main():
    start_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        logging.info("Job started")

        # Load config
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)

        required_fields = ["seed", "window", "version"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing config field: {field}")

        np.random.seed(config["seed"])

        logging.info(
            f"Config loaded: seed={config['seed']}, "
            f"window={config['window']}, "
            f"version={config['version']}"
        )

        # Load dataset
        raw_df = pd.read_csv(args.input, header=None)

        # Split quoted CSV rows
        df = raw_df[0].str.split(",", expand=True)

        # Set header
        df.columns = df.iloc[0]

        # Remove header row
        df = df[1:].reset_index(drop=True)

        if df.empty:
            raise ValueError("Input CSV is empty")

        if "close" not in df.columns:
            raise ValueError("Missing required column: close")

        # Convert close to numeric
        df["close"] = pd.to_numeric(df["close"])

        logging.info(f"Rows loaded: {len(df)}")

        # Rolling mean
        df["rolling_mean"] = (
            df["close"]
            .rolling(window=config["window"])
            .mean()
        )

        logging.info("Rolling mean computed")

        # Signal generation
        df["signal"] = (
            df["close"] > df["rolling_mean"]
        ).astype(int)

        logging.info("Signal generation completed")

        # Metrics
        signal_rate = float(df["signal"].mean())

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        metrics = {
            "version": config["version"],
            "rows_processed": int(len(df)),
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "latency_ms": latency_ms,
            "seed": config["seed"],
            "status": "success"
        }

        with open(args.output, "w") as f:
            json.dump(metrics, f, indent=4)

        logging.info(f"Metrics summary: {metrics}")
        logging.info("Job completed successfully")

        print(json.dumps(metrics, indent=4))

    except Exception as e:

        error_metrics = {
            "version": "v1",
            "status": "error",
            "error_message": str(e)
        }

        with open(args.output, "w") as f:
            json.dump(error_metrics, f, indent=4)

        logging.error(str(e))

        print(json.dumps(error_metrics, indent=4))


if __name__ == "__main__":
    main()