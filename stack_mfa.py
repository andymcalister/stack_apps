"""
Stack MFA Module — TOTP (Google Authenticator / Authy)
Free, no SMS, works offline.
"""
import streamlit as st
import pyotp
import qrcode
import io
import base64
from PIL import Image


def generate_totp_secret() -> str:
    """Generate a new TOTP secret for a user."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Get the otpauth URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name="Stack Financial"
    )


def generate_qr_code(uri: str) -> str:
    """Generate QR code as base64 PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(
        fill_color="#00C2A8",
        back_color="#0A1628"
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code. Allows 1 window either side for clock drift."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def render_mfa_setup(email: str, supabase, user_id: str):
    """
    Render the MFA setup flow.
    Returns True if MFA was successfully enabled.
    """
    st.markdown("""
    <div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;
        margin-bottom:0.5rem;color:#FFFFFF">Set Up Two-Factor Authentication</div>
    <div style="color:#94A3B8;font-size:0.9rem;margin-bottom:1.5rem;line-height:1.7">
        Scan the QR code below with <strong style="color:#FFFFFF">Google Authenticator</strong>,
        <strong style="color:#FFFFFF">Authy</strong>, or any TOTP app.
        Then enter the 6-digit code to confirm setup.
    </div>
    """, unsafe_allow_html=True)

    # Generate secret if not already in session
    if "mfa_setup_secret" not in st.session_state:
        st.session_state.mfa_setup_secret = generate_totp_secret()

    secret = st.session_state.mfa_setup_secret
    uri    = get_totp_uri(secret, email)
    qr_b64 = generate_qr_code(uri)

    # Show QR code
    col_qr, col_inst = st.columns([1, 1.5])
    with col_qr:
        st.markdown(f"""
        <div style="background:#0A1628;border:2px solid rgba(0,194,168,0.3);
            border-radius:14px;padding:1rem;display:inline-block;text-align:center">
            <img src="data:image/png;base64,{qr_b64}" width="200">
        </div>
        """, unsafe_allow_html=True)

    with col_inst:
        st.markdown("""
        <div style="background:rgba(15,32,53,0.7);border-radius:12px;
            padding:1.25rem;border:1px solid rgba(255,255,255,0.07)">
            <div style="font-weight:700;margin-bottom:0.75rem;color:#E2EDF4">
                Steps:
            </div>
            <div style="font-size:0.85rem;color:#94A3B8;line-height:2">
                1. Download <strong style="color:#FFFFFF">Google Authenticator</strong>
                   or <strong style="color:#FFFFFF">Authy</strong><br>
                2. Tap <strong style="color:#FFFFFF">+</strong> → Scan QR code<br>
                3. Point your camera at the code<br>
                4. Enter the <strong style="color:#00C2A8">6-digit code</strong> below
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Manual entry backup
        with st.expander("Can't scan? Enter code manually"):
            st.markdown(f"""
            <div style="font-family:monospace;font-size:0.85rem;
                background:rgba(0,194,168,0.06);padding:0.75rem;
                border-radius:8px;color:#00C2A8;letter-spacing:0.1em;
                word-break:break-all">{secret}</div>
            """, unsafe_allow_html=True)
            st.caption("Enter this key manually in your authenticator app")

    st.markdown("<br>", unsafe_allow_html=True)
    code = st.text_input(
        "Enter the 6-digit code from your app",
        key="mfa_setup_code",
        placeholder="000000",
        max_chars=6
    )

    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("✅ Enable MFA", key="enable_mfa", use_container_width=True):
            if not code or len(code) != 6 or not code.isdigit():
                st.error("Please enter a valid 6-digit code.")
            elif verify_totp(secret, code):
                # Save to Supabase
                supabase.table("users").update({
                    "totp_secret":  secret,
                    "mfa_enabled":  True,
                    "mfa_verified": True,
                }).eq("id", user_id).execute()
                del st.session_state.mfa_setup_secret
                st.success("✅ MFA enabled! Your account is now protected.")
                return True
            else:
                st.error("Incorrect code. Please check your app and try again.")
    with col_b:
        if st.button("Skip for now →", key="skip_mfa", use_container_width=True):
            return False

    return False


def render_mfa_verify(secret: str) -> bool:
    """
    Render the MFA verification prompt at login.
    Returns True if code is correct.
    """
    st.markdown("""
    <div style="text-align:center;padding:1rem 0">
        <div style="font-size:2.5rem;margin-bottom:0.75rem">🔐</div>
        <div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;
            color:#FFFFFF;margin-bottom:0.5rem">Two-Factor Verification</div>
        <div style="color:#94A3B8;font-size:0.875rem;margin-bottom:1.5rem">
            Enter the 6-digit code from your authenticator app
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, mc, _ = st.columns([1, 2, 1])
    with mc:
        code = st.text_input(
            "Authentication code",
            key="mfa_verify_code",
            placeholder="000000",
            max_chars=6,
            label_visibility="collapsed"
        )
        if st.button("Verify →", key="verify_mfa", use_container_width=True):
            if not code or len(code) != 6 or not code.isdigit():
                st.error("Please enter a valid 6-digit code.")
            elif verify_totp(secret, code):
                return True
            else:
                st.error("Incorrect code. Please try again.")
    return False
