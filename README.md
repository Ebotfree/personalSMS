# SMS Personalizados para Chile (+56)

Herramienta en Python para enviar SMS personalizados a contactos de Chile (prefijo `+56`) usando Twilio.

## Requisitos

- Python 3.9+
- Credenciales de Twilio:
  - `Account SID`
  - `Auth Token`
  - Número remitente de Twilio

Instala dependencias:

```bash
pip install -r requirements.txt
```

## Formato del CSV

El CSV debe tener cabeceras. Por defecto la columna del teléfono debe llamarse `phone`.
Puedes incluir todas las columnas que quieras para personalizar el mensaje.

Ejemplo `contactos.csv`:

```csv
phone,nombre,codigo
+56912345678,Ana,8492
+56987654321,Carlos,1190
```

## Uso

```bash
python sms_personalizados.py \
  --csv contactos.csv \
  --template "Hola {nombre}, tu código es {codigo}" \
  --from-number "+15005550006" \
  --account-sid "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  --auth-token "tu_auth_token"
```

## Validaciones

- Solo envía a números válidos con prefijo `+56`.
- Si un número no cumple formato, se omite y se reporta.
- Si falta una columna usada por la plantilla, el proceso se detiene con error.

## Modo de prueba (sin envío real)

```bash
python sms_personalizados.py \
  --csv contactos.csv \
  --template "Hola {nombre}, tu código es {codigo}" \
  --from-number "+15005550006" \
  --account-sid "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  --auth-token "tu_auth_token" \
  --dry-run
```
