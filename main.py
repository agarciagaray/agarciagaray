from __future__ import annotations

import base64
import os
from pathlib import Path

import flet as ft
from sqlalchemy import select

from db import Account, AppConfig, Bank, Card, SessionLocal, init_db
from security import decrypt, derive_key, encrypt, mask, new_key_material

APP_NAME = "Bóveda Bancaria"
ASSET_DIR = Path(os.getenv("DATA_DIR", "data")) / "logos"
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def main(page: ft.Page):
    page.title = APP_NAME
    page.window.width = 1260
    page.window.height = 820
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    state = {"key": None, "selected": None, "reveal": False, "logo": None}
    init_db()

    def toast(message: str, error: bool = False):
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700, open=True)
        page.update()

    def dialog(title, content, actions):
        page.dialog = ft.AlertDialog(title=ft.Text(title), content=content, actions=actions, modal=True)
        page.dialog.open = True
        page.update()

    def setup():
        with SessionLocal() as s:
            cfg = s.get(AppConfig, 1)
        if cfg:
            login_view()
        else:
            first_run_view()

    def first_run_view():
        password = ft.TextField(label="Contraseña maestra", password=True, can_reveal_password=True, autofocus=True)
        confirm = ft.TextField(label="Confirmar contraseña", password=True, can_reveal_password=True)
        def create(_):
            if password.value != confirm.value:
                toast("Las contraseñas no coinciden", True); return
            try:
                km = new_key_material(password.value)
                with SessionLocal.begin() as s:
                    s.add(AppConfig(id=1, salt_b64=base64.b64encode(km.salt).decode()))
                state["key"] = km.key
                app_view(); toast("Bóveda creada. La contraseña no se puede recuperar.")
            except ValueError as e: toast(str(e), True)
        page.clean(); page.add(ft.Container(expand=True, alignment=ft.alignment.center, content=ft.Column([
            ft.Icon(ft.Icons.LOCK_ROUNDED, size=64, color=ft.Colors.INDIGO_300), ft.Text(APP_NAME, size=34, weight=ft.FontWeight.BOLD),
            ft.Text("Crea la contraseña maestra que protegerá todos tus datos.", color=ft.Colors.GREY_400), password, confirm,
            ft.FilledButton("Crear bóveda", icon=ft.Icons.SECURITY, on_click=create, width=320),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18)))
        page.update()

    def login_view():
        password = ft.TextField(label="Contraseña maestra", password=True, can_reveal_password=True, autofocus=True)
        def login(_):
            try:
                with SessionLocal() as s: cfg = s.get(AppConfig, 1)
                state["key"] = derive_key(password.value, base64.b64decode(cfg.salt_b64))
                app_view()
            except Exception: toast("Contraseña incorrecta o configuración inválida", True)
        page.clean(); page.add(ft.Container(expand=True, alignment=ft.alignment.center, content=ft.Column([
            ft.Icon(ft.Icons.SHIELD_ROUNDED, size=64, color=ft.Colors.INDIGO_300), ft.Text(APP_NAME, size=34, weight=ft.FontWeight.BOLD),
            ft.Text("Acceso protegido", color=ft.Colors.GREY_400), password, ft.FilledButton("Desbloquear", icon=ft.Icons.LOCK_OPEN, on_click=login, width=320),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18))); page.update()

    def app_view():
        selected = ft.Ref[ft.Dropdown](); name = ft.Ref[ft.TextField](); owner = ft.Ref[ft.TextField](); branch = ft.Ref[ft.TextField](); virtual = ft.Ref[ft.Switch]()
        account_no = ft.Ref[ft.TextField](); breb = ft.Ref[ft.TextField](); phone = ft.Ref[ft.TextField](); pin = ft.Ref[ft.TextField]()
        card_type = ft.Ref[ft.Dropdown](); card_no = ft.Ref[ft.TextField](); expiry = ft.Ref[ft.TextField](); cvc = ft.Ref[ft.TextField](); variable = ft.Ref[ft.Checkbox](); variable_hint = ft.Ref[ft.TextField]()
        cards = ft.Ref[ft.Column](); logo_text = ft.Ref[ft.Text](); banks_list = ft.Ref[ft.Column]()
        state["selected"] = None

        def refresh():
            banks_list.current.controls.clear()
            with SessionLocal() as s: banks = list(s.scalars(select(Bank).order_by(Bank.name)))
            if not banks: banks_list.current.controls.append(ft.Text("Aún no hay bancos registrados.", color=ft.Colors.GREY_500))
            for b in banks:
                banks_list.current.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.ACCOUNT_BALANCE), title=ft.Text(b.name), subtitle=ft.Text(f"{len(b.accounts)} cuenta(s)"), on_click=lambda e, bid=b.id: load_bank(bid)))
            page.update()

        def load_bank(bid):
            with SessionLocal() as s: b = s.get(Bank, bid)
            state["selected"] = bid; name.current.value=b.name; owner.current.value=b.owner_name; branch.current.value=b.branch; virtual.current.value=b.is_virtual
            account_no.current.value=breb.current.value=phone.current.value=pin.current.value=""; cards.current.controls.clear(); logo_text.current.value=b.logo_path or "Sin imagen"
            if b.accounts:
                a=b.accounts[0]
                account_no.current.value=mask(decrypt(a.account_number_enc,state["key"]))
                breb.current.value=mask(decrypt(a.breb_key_enc,state["key"])) if a.breb_key_enc else ""
                phone.current.value=mask(decrypt(a.phone_key_enc,state["key"])) if a.phone_key_enc else ""
                pin.current.value="••••" if a.withdrawal_pin_enc else ""
                for c in a.cards: add_card_row(c)
            page.update()

        def add_card_row(c=None):
            vals = [c.card_type if c else "Débito", mask(decrypt(c.number_enc,state["key"])) if c else "", mask(decrypt(c.expiry_enc,state["key"])) if c else "", "Variable" if c and c.cvc_variable else mask(decrypt(c.cvc_enc,state["key"])) if c else ""]
            cards.current.controls.append(ft.DataRow(cells=[ft.DataCell(ft.Text(x)) for x in vals])); page.update()

        def save(_):
            if not name.current.value or not owner.current.value or not account_no.current.value: toast("Banco, dueño y número de cuenta son obligatorios", True); return
            try:
                with SessionLocal.begin() as s:
                    b=s.get(Bank,state["selected"]) if state["selected"] else Bank(name=name.current.value,owner_name=owner.current.value,branch=branch.current.value or "",is_virtual=virtual.current.value)
                    b.name=name.current.value; b.owner_name=owner.current.value; b.branch=branch.current.value or ""; b.is_virtual=virtual.current.value
                    if logo_text.current.value != "Sin imagen": b.logo_path = logo_text.current.value
                    if not state["selected"]: s.add(b); s.flush()
                    a=b.accounts[0] if b.accounts else Account(bank_id=b.id,account_number_enc="")
                    a.account_number_enc=encrypt(account_no.current.value,state["key"]); a.breb_key_enc=encrypt(breb.current.value,state["key"]); a.phone_key_enc=encrypt(phone.current.value,state["key"]); a.withdrawal_pin_enc=encrypt(pin.current.value,state["key"])
                    if not b.accounts: s.add(a)
                state["selected"]=b.id; refresh(); toast("Datos guardados de forma cifrada")
            except Exception as e: toast(f"No fue posible guardar: {e}", True)

        def reveal(_):
            password=ft.TextField(label="Confirma la contraseña maestra",password=True,can_reveal_password=True)
            def ok(_):
                try:
                    with SessionLocal() as s: cfg=s.get(AppConfig,1)
                    if derive_key(password.value,base64.b64decode(cfg.salt_b64)) != state["key"]: raise ValueError()
                    state["reveal"]=True; dialog("Datos revelados", ft.Text("La vista se desbloqueó para esta sesión. Cierra la sesión al terminar."), [ft.TextButton("Cerrar", on_click=lambda e: setattr(page.dialog,"open",False))]); page.update()
                except Exception: toast("Contraseña incorrecta", True)
            dialog("Autenticación requerida", ft.Column([ft.Text("Por seguridad, confirma tu contraseña para revelar secretos."),password]), [ft.TextButton("Cancelar",on_click=lambda e:setattr(page.dialog,"open",False)),ft.FilledButton("Revelar",on_click=ok)])

        def pick_logo(e):
            if not e.files: return
            src = Path(e.files[0].path)
            if src.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                toast("El logo debe ser PNG o JPG", True); return
            dest = ASSET_DIR / f"bank_{state.get('selected') or 'new'}{src.suffix.lower()}"
            dest.write_bytes(src.read_bytes())
            logo_text.current.value = str(dest)
            page.update()

        logo_picker = ft.FilePicker(on_result=pick_logo)
        page.overlay.append(logo_picker)

        def new_bank(_):
            state["selected"] = None
            for ref in (name, owner, branch, account_no, breb, phone, pin): ref.current.value = ""
            virtual.current.value = False; cards.current.controls.clear(); logo_text.current.value = "Sin imagen"; page.update()

        def toggle_theme(_): page.theme_mode=ft.ThemeMode.LIGHT if page.theme_mode==ft.ThemeMode.DARK else ft.ThemeMode.DARK; page.update()
        fields=ft.Column([ft.Text("Datos principales",size=20,weight=ft.FontWeight.BOLD),ft.Row([ft.TextField(ref=name,label="Nombre del banco",expand=1),ft.TextField(ref=owner,label="Dueño de la cuenta",expand=1)]),ft.Row([ft.TextField(ref=branch,label="Sucursal",expand=1),ft.Switch(ref=virtual,label="Cuenta virtual")]),ft.Row([ft.Text(ref=logo_text,value="Sin imagen",color=ft.Colors.GREY_500,expand=1),ft.OutlinedButton("Subir logo PNG/JPG",icon=ft.Icons.IMAGE,on_click=lambda e: logo_picker.pick_files(allowed_extensions=["png","jpg","jpeg"]))]),ft.Divider(),ft.Text("Cuenta",size=20,weight=ft.FontWeight.BOLD),ft.Row([ft.TextField(ref=account_no,label="Número de cuenta",password=True,can_reveal_password=True,expand=1),ft.TextField(ref=breb,label="Llave Bre-B",password=True,can_reveal_password=True,expand=1)]),ft.Row([ft.TextField(ref=phone,label="Clave telefónica",password=True,can_reveal_password=True,expand=1),ft.TextField(ref=pin,label="Clave de retiros / acceso",password=True,can_reveal_password=True,expand=1)]),ft.Divider(),ft.Row([ft.Text("Tarjetas",size=20,weight=ft.FontWeight.BOLD),ft.OutlinedButton("Agregar tarjeta",icon=ft.Icons.ADD,on_click=lambda e:add_card_row())]),ft.DataTable(columns=[ft.DataColumn(ft.Text("Tipo")),ft.DataColumn(ft.Text("Número")),ft.DataColumn(ft.Text("Vencimiento")),ft.DataColumn(ft.Text("CVC / CCV"))],rows=cards),ft.Row([ft.FilledButton("Guardar cambios",icon=ft.Icons.SAVE,on_click=save),ft.OutlinedButton("Revelar secretos",icon=ft.Icons.VISIBILITY,on_click=reveal)])],scroll=ft.ScrollMode.AUTO,expand=True)
        page.clean(); page.add(ft.Row([ft.Container(width=290,padding=24,bgcolor=ft.Colors.with_opacity(.06,ft.Colors.INDIGO_200),content=ft.Column([ft.Row([ft.Icon(ft.Icons.SHIELD),ft.Text(APP_NAME,size=20,weight=ft.FontWeight.BOLD)]),ft.Row([ft.Text("Bancos",size=18,weight=ft.FontWeight.BOLD),ft.IconButton(ft.Icons.ADD,on_click=new_bank)]),ft.Column(ref=banks_list),ft.Container(expand=True),ft.TextButton("Cambiar tema",icon=ft.Icons.DARK_MODE,on_click=toggle_theme),ft.TextButton("Bloquear sesión",icon=ft.Icons.LOCK,on_click=lambda e:login_view())])),ft.Container(expand=True,padding=32,content=fields)])); refresh()

    setup()

if __name__ == "__main__":
    ft.app(target=main)
