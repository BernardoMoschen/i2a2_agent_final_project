"""Cloud-compatible report generation using in-memory BytesIO."""

import logging
from io import BytesIO, StringIO
from typing import Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class InMemoryReportGenerator:
    """Generate reports in memory for Streamlit Cloud compatibility."""

    @staticmethod
    def generate_csv(df: pd.DataFrame, filename: str = "report") -> Dict[str, Any]:
        """
        Generate CSV report in memory.

        Args:
            df: DataFrame to export
            filename: Base filename (without extension)

        Returns:
            Dict with keys: type, filename, content (bytes), mime
        """
        try:
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            return {
                "type": "csv",
                "filename": f"{filename}.csv",
                "content": csv_bytes,
                "mime": "text/csv"
            }
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            raise

    @staticmethod
    def generate_excel(df: pd.DataFrame, filename: str = "report") -> Dict[str, Any]:
        """
        Generate Excel report in memory.

        Args:
            df: DataFrame to export
            filename: Base filename (without extension)

        Returns:
            Dict with keys: type, filename, content (bytes), mime
        """
        try:
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
            
            excel_bytes = excel_buffer.getvalue()
            
            return {
                "type": "xlsx",
                "filename": f"{filename}.xlsx",
                "content": excel_bytes,
                "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        except Exception as e:
            logger.error(f"Error generating Excel: {e}")
            raise

    @staticmethod
    def generate_parquet(df: pd.DataFrame, filename: str = "report") -> Dict[str, Any]:
        """
        Generate Parquet report in memory.

        Args:
            df: DataFrame to export
            filename: Base filename (without extension)

        Returns:
            Dict with keys: type, filename, content (bytes), mime
        """
        try:
            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            parquet_bytes = parquet_buffer.getvalue()
            
            return {
                "type": "parquet",
                "filename": f"{filename}.parquet",
                "content": parquet_bytes,
                "mime": "application/octet-stream"
            }
        except Exception as e:
            logger.error(f"Error generating Parquet: {e}")
            raise

    @staticmethod
    def generate_report(
        df: pd.DataFrame,
        filename: str = "report",
        format: str = "csv"
    ) -> Dict[str, Any]:
        """
        Generate report in specified format.

        Args:
            df: DataFrame to export
            filename: Base filename (without extension)
            format: 'csv', 'xlsx', or 'parquet'

        Returns:
            Dict with report metadata and content bytes
        """
        if format.lower() in ['csv', 'text/csv']:
            return InMemoryReportGenerator.generate_csv(df, filename)
        elif format.lower() in ['xlsx', 'excel', 'xls', 
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return InMemoryReportGenerator.generate_excel(df, filename)
        elif format.lower() in ['parquet', 'pq', 'application/octet-stream']:
            return InMemoryReportGenerator.generate_parquet(df, filename)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv', 'xlsx', or 'parquet'")
