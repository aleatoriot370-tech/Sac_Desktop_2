"""
SAC - Grupo Lamoia
Entry point: Flask + PyWebView.

Flask roda em thread separada; PyWebView abre a janela nativa apontando
para http://127.0.0.1:<porta>.
"""
import sys
import socket
import threading
from pathlib import Path

# Adiciona o diretório raiz ao path para imports locais
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
import webview

from backend.routes import bp as api_bp
from config import Config


def resource_path(relative_path: str) -> Path:
    """Resolve paths para desenvolvimento e PyInstaller (sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    return Path(base) / relative_path


def _find_free_port() -> int:
    """Encontra uma porta TCP livre no localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def create_app() -> Flask:
    """Factory Flask."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "frontend" / "templates"),
        static_folder=str(Path(__file__).parent / "frontend" / "static"),
    )
    app.config["SECRET_KEY"] = "sac-grupo-lamoia-dev"
    app.config["JSON_AS_ASCII"] = False

    # Registra o blueprint da API
    app.register_blueprint(api_bp)

    # Rota principal → serve o SPA
    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    return app


def main():
    app = create_app()
    port = _find_free_port()

    # Flask em thread separada (não bloqueia o PyWebView)
    server_thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    server_thread.start()

    # Janela nativa via PyWebView
    window = webview.create_window(
        title=Config.APP_NAME,
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=800,
        resizable=True,
        min_size=(900, 600),
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
