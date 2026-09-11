# Bóveda Bancaria

Aplicación de escritorio en Python y Flet para administrar cuentas bancarias, tarjetas y credenciales sensibles. La interfaz usa un diseño Material 3 con apariencia compacta de escritorio, temas claro y oscuro, navegación lateral, mensajes tipo toast y diálogos de confirmación.

## Seguridad

Los números de cuenta, números de tarjeta, vencimientos, CVC/CCV, llave Bre-B, clave telefónica y clave de retiros **no se almacenan en texto plano**. La contraseña maestra se usa para derivar una clave mediante Argon2id. Cada secreto se cifra con AES-256-GCM y un nonce aleatorio. La contraseña no se puede recuperar ni se persiste.

La revelación de secretos exige volver a introducir la contraseña maestra. La aplicación muestra datos enmascarados por defecto. La base local SQLite sirve para desarrollo; en despliegues reales se debe usar MariaDB mediante `DATABASE_URL` y restringir el acceso de la base de datos a la máquina o red privada.

> El CVC es un dato de autenticación de tarjeta. Debe almacenarse solo si existe una necesidad legítima y conforme con las políticas del emisor y los requisitos PCI DSS. No se debe usar esta aplicación como sistema de procesamiento de pagos.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Para MariaDB, cree la base y un usuario con permisos mínimos, luego cambie `DATABASE_URL`:

```env
DATABASE_URL=mysql+pymysql://boveda_app:CAMBIAR@127.0.0.1:3306/boveda_bancaria?charset=utf8mb4
```

## Modelo funcional

| Entidad | Datos |
|---|---|
| Banco | Nombre, propietario, sucursal, indicador virtual e imagen |
| Cuenta | Número cifrado, llave Bre-B cifrada, clave telefónica cifrada y clave de retiros cifrada |
| Tarjeta | Tipo, número cifrado, vencimiento cifrado, CVC cifrado o indicador de CVC variable y pista cifrada |

## Próximos incrementos recomendados

La base está preparada para añadir una pantalla de edición de tarjetas con carga de imagen PNG/JPG validada, exportación cifrada, auditoría de accesos, bloqueo por inactividad y soporte de llaves del sistema operativo. Para una versión de producción se recomienda completar esas funciones, añadir migraciones Alembic, pruebas de integración contra MariaDB y una revisión independiente de seguridad.
