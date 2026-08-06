"""
SAC - Grupo Lamoia
Entry point: Flask web application.

Roda como servidor web acessível no navegador.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports locais
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from backend.routes import bp as api_bp
from config import Config


def create_app() -> Flask:
    """Factory Flask."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "frontend" / "templates"),
        static_folder=str(Path(__file__).parent / "frontend" / "static"),
    )
    app.config["SECRET_KEY"] = Config.SECRET_KEY or "sac-grupo-lamoia-dev"
    app.config["JSON_AS_ASCII"] = False

    # Registra o blueprint da API
    app.register_blueprint(api_bp)

    # Rota principal → serve o SPA
    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SAC - Grupo Lamoia")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Porta (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Modo debug")
    args = parser.parse_args()

    app = create_app()
    print(f"\n{'='*50}")
    print(f"  SAC - Grupo Lamoia")
    print(f"  Acesse: http://{args.host}:{args.port}")
    print(f"{'='*50}\n")
    app.run(host=args.host, port=args.port, debug=args.debug)
