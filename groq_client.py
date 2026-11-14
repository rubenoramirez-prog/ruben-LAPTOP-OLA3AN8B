#!/usr/bin/env python3
"""
Cliente y Adaptador de Groq Cloud para LLMs Gratuitos.
Cumple con estandares L3 y arquitectura limpia.
"""

import os
import sys
from typing import Optional
import click
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
RECOMMENDED_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]


class GroqAdapter:
    """Adaptador de infraestructura para inferencia con Groq Cloud."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key or self.api_key == "gsk_tu_clave_aqui":
            raise ValueError(
                "API Key no configurada. Define GROQ_API_KEY en tu archivo .env "
                "o en las variables de entorno. Obtenla gratis en: https://console.groq.com/keys"
            )
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("Libreria 'groq' no instalada. Ejecuta: pip install groq")

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Eres un asistente de IA tecnico, preciso y conciso.",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Envia una solicitud de completado a Groq y retorna el texto generado."""
        if not prompt or not prompt.strip():
            raise ValueError("El prompt no puede estar vacio.")

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(f"Fallo en la llamada a Groq API ({model}): {exc}") from exc


@click.group()
def cli():
    """CLI para interactuar con Groq Cloud (Modelos Gratuitos Llama 3.3 y DeepSeek)."""
    pass


@cli.command("test")
@click.option("--model", default=DEFAULT_MODEL, help="Modelo a evaluar.")
def test_cmd(model: str):
    """Ejecuta un smoke-test rapido de conectividad."""
    click.echo(f"[*] Iniciando smoke test con Groq API ({model})...")
    try:
        adapter = GroqAdapter()
        res = adapter.generate(
            prompt="Responde 'Conexion OK con Groq' e indica tu modelo y latencia percibida en 1 linea.",
            model=model,
            max_tokens=100,
        )
        click.secho(f"[✓] Exito:\n{res}", fg="green")
    except Exception as e:
        click.secho(f"[✗] Error: {e}", fg="red")
        sys.exit(1)


@cli.command("prompt")
@click.argument("text")
@click.option("--model", default=DEFAULT_MODEL, help="Modelo a utilizar.")
@click.option("--system", default="Eres un asistente tecnico conciso.", help="System prompt.")
@click.option("--temp", default=0.2, type=float, help="Temperatura (0.0 a 1.0).")
def prompt_cmd(text: str, model: str, system: str, temp: float):
    """Envia un prompt a Groq y muestra la respuesta."""
    try:
        adapter = GroqAdapter()
        res = adapter.generate(prompt=text, system_prompt=system, model=model, temperature=temp)
        click.echo(res)
    except Exception as e:
        click.secho(f"[✗] Error: {e}", fg="red")
        sys.exit(1)


@cli.command("models")
def list_models_cmd():
    """Muestra los modelos disponibles en tu cuenta de Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key != "gsk_tu_clave_aqui":
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            models = [m.id for m in client.models.list().data]
            click.echo("\nModelos activos y accesibles en tu cuenta de Groq:")
            for m in models:
                prefix = "-> (Default) " if m == DEFAULT_MODEL else "   "
                click.echo(f"{prefix}{m}")
            click.echo("")
            return
        except Exception:
            pass

    click.echo("\nModelos recomendados con tier gratuito en Groq:")
    for m in RECOMMENDED_MODELS:
        prefix = "-> (Default) " if m == DEFAULT_MODEL else "   "
        click.echo(f"{prefix}{m}")
    click.echo("\nMas info: https://console.groq.com/docs/models\n")


if __name__ == "__main__":
    cli()
