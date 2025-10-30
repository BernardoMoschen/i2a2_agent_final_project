"""Simple file server for report downloads."""

import logging
from pathlib import Path
from typing import Optional

from flask import Flask, send_file, abort

logger = logging.getLogger(__name__)


class ReportFileServer:
    """Serve report files from the reports directory."""

    def __init__(self, reports_dir: str = "./reports"):
        """Initialize file server.
        
        Args:
            reports_dir: Path to reports directory
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.app = Flask(__name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes."""
        
        @self.app.route('/download/<filename>')
        def download_file(filename: str):
            """Download a report file.
            
            Args:
                filename: Name of file to download
                
            Returns:
                File for download or 404 error
            """
            try:
                # Security: prevent directory traversal
                if '..' in filename or '/' in filename:
                    abort(400)
                
                file_path = self.reports_dir / filename
                
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    abort(404)
                
                # Determine mimetype
                if filename.endswith('.xlsx'):
                    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif filename.endswith('.csv'):
                    mimetype = 'text/csv'
                elif filename.endswith('.png'):
                    mimetype = 'image/png'
                else:
                    mimetype = 'application/octet-stream'
                
                logger.info(f"Serving file: {file_path}")
                return send_file(
                    file_path,
                    as_attachment=True,
                    mimetype=mimetype,
                    download_name=filename
                )
            
            except Exception as e:
                logger.error(f"Error downloading file {filename}: {e}", exc_info=True)
                abort(500)
        
        @self.app.route('/health')
        def health():
            """Health check endpoint."""
            return {'status': 'ok'}, 200
    
    def get_download_url(self, filename: str, port: int = 5000) -> str:
        """Get download URL for a file.
        
        Args:
            filename: Name of file
            port: Port of Flask server
            
        Returns:
            Download URL
        """
        return f"http://localhost:{port}/download/{filename}"
    
    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Run the Flask server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        logger.info(f"Starting file server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
