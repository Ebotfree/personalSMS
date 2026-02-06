#!/usr/bin/env python3
"""Herramienta CLI para enviar SMS personalizados a números con prefijo +56."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict

CHILE_PHONE_REGEX = re.compile(r"^\+56\d{8,9}$")


@dataclass
class TwilioConfig:
    account_sid: str
    auth_token: str
    from_number: str


class SmsError(Exception):
    """Excepción controlada para errores de envío de SMS."""


def validar_numero_chile(numero: str) -> bool:
    return bool(CHILE_PHONE_REGEX.fullmatch(numero.strip()))


def enviar_sms_twilio(config: TwilioConfig, to_number: str, body: str) -> str:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}/Messages.json"
    data = urllib.parse.urlencode({"To": to_number, "From": config.from_number, "Body": body}).encode()

    token = f"{config.account_sid}:{config.auth_token}".encode("utf-8")
    auth_header = base64.b64encode(token).decode("ascii")

    request = urllib.request.Request(url=url, data=data, method="POST")
    request.add_header("Authorization", f"Basic {auth_header}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SmsError(f"Twilio respondió con error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SmsError(f"No fue posible conectar con Twilio: {exc.reason}") from exc

    sid = payload.get("sid")
    if not sid:
        raise SmsError(f"Respuesta inesperada de Twilio: {payload}")

    return sid


def render_template(template: str, row: Dict[str, str]) -> str:
    try:
        return template.format(**row)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise SmsError(
            f"La plantilla requiere la columna '{{{missing_key}}}' en el CSV y no fue encontrada."
        ) from exc


def procesar_envios(
    csv_path: str,
    template: str,
    config: TwilioConfig,
    phone_column: str,
    dry_run: bool,
) -> int:
    enviados = 0

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise SmsError("El archivo CSV no contiene cabeceras.")
        if phone_column not in reader.fieldnames:
            raise SmsError(
                f"No existe la columna '{phone_column}' en el CSV. "
                f"Columnas disponibles: {', '.join(reader.fieldnames)}"
            )

        for idx, row in enumerate(reader, start=2):
            numero = (row.get(phone_column) or "").strip()

            if not validar_numero_chile(numero):
                print(f"[Línea {idx}] Número inválido (debe iniciar con +56): {numero}", file=sys.stderr)
                continue

            mensaje = render_template(template, row)

            if dry_run:
                print(f"[DRY RUN] {numero} <- {mensaje}")
                enviados += 1
                continue

            sid = enviar_sms_twilio(config=config, to_number=numero, body=mensaje)
            print(f"[OK] Enviado a {numero}. SID: {sid}")
            enviados += 1

    return enviados


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Envía SMS personalizados a números de Chile (+56) usando Twilio."
    )
    parser.add_argument("--csv", required=True, help="Ruta al archivo CSV con los destinatarios.")
    parser.add_argument(
        "--template",
        required=True,
        help="Plantilla del mensaje. Ejemplo: 'Hola {nombre}, tu código es {codigo}'.",
    )
    parser.add_argument(
        "--phone-column",
        default="phone",
        help="Nombre de la columna del CSV que contiene el número de destino. Por defecto: phone.",
    )
    parser.add_argument("--from-number", required=True, help="Número remitente (Twilio).")
    parser.add_argument("--account-sid", required=True, help="Account SID de Twilio.")
    parser.add_argument("--auth-token", required=True, help="Auth Token de Twilio.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No envía SMS reales; solo muestra qué mensajes se enviarían.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = TwilioConfig(
        account_sid=args.account_sid,
        auth_token=args.auth_token,
        from_number=args.from_number,
    )

    try:
        total = procesar_envios(
            csv_path=args.csv,
            template=args.template,
            config=config,
            phone_column=args.phone_column,
            dry_run=args.dry_run,
        )
    except SmsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo CSV '{args.csv}'.", file=sys.stderr)
        return 1

    print(f"Proceso finalizado. Mensajes procesados: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
