"""
Combine filtered ATS chain CSV logs into a single output CSV.

- From logs_ats2tmp.csv: keep rows where 'X-Request-Type' does NOT contain 'APACHETRAFFICSERVER_'.
- From logs_ats2httpd.csv: keep rows where 'X-Request-Type' contains 'APACHETRAFFICSERVER_APACHEHTTPSERVER'.
- From logs_ats2tomcat.csv: keep rows where 'X-Request-Type' contains 'APACHETRAFFICSERVER_APACHETOMCAT'.
- From logs_ats2nginx.csv: keep rows where 'X-Request-Type' contains 'APACHETRAFFICSERVER_NGINX'.

Usage:
    python get_combined_logs_csv.py \
      --tmp    path/to/logs_ats2tmp.csv \
      --httpd  path/to/logs_ats2httpd.csv \
      --tomcat path/to/logs_ats2tomcat.csv \
      --nginx  path/to/logs_ats2nginx.csv \
      --output path/to/combined_logs.csv
"""

import argparse
import os
import pandas as pd

def filter_df(df: pd.DataFrame, column: str, contains: str | None) -> pd.DataFrame:
    if contains is None:
        # invert=True means rows that do NOT contain 'APACHETRAFFICSERVER_'
        mask = ~df[column].str.contains('APACHETRAFFICSERVER_', na=False)
    else:
        mask = df[column].str.contains(contains, na=False)
    return df[mask]

def main():
    parser = argparse.ArgumentParser(description="Combine filtered rows from ATS chain CSVs")
    parser.add_argument("--tmp",    required=True, help="Path to logs_ats2tmp.csv")
    parser.add_argument("--httpd",  required=True, help="Path to logs_ats2httpd.csv")
    parser.add_argument("--tomcat", required=True, help="Path to logs_ats2tomcat.csv")
    parser.add_argument("--nginx",  required=True, help="Path to logs_ats2nginx.csv")
    parser.add_argument("--output", required=True, help="Path to write the combined CSV")
    args = parser.parse_args()

    # Load each CSV
    df_tmp    = pd.read_csv(args.tmp)
    df_httpd  = pd.read_csv(args.httpd)
    df_tomcat = pd.read_csv(args.tomcat)
    df_nginx  = pd.read_csv(args.nginx)

    col = "X-Request-Type"
    # Apply filters
    filtered_tmp    = filter_df(df_tmp,    col, contains=None)
    filtered_httpd  = filter_df(df_httpd,  col, contains="APACHETRAFFICSERVER2APACHEHTTPSERVER_APACHEHTTPSERVER")
    filtered_tomcat = filter_df(df_tomcat, col, contains="APACHETRAFFICSERVER2APACHETOMCAT_APACHETOMCAT")
    filtered_nginx  = filter_df(df_nginx,  col, contains="APACHETRAFFICSERVER2NGINX_NGINX")

    # Combine and write
    combined = pd.concat([filtered_tmp, filtered_httpd, filtered_tomcat, filtered_nginx], ignore_index=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    combined.to_csv(args.output, index=False)

    print(f"[✅ Combined] {len(combined)} total rows written to {args.output}")

if __name__ == "__main__":
    main()