"""
Shared UI styles and components for AI Testcase Generator.
Provides the Neural Test Lab design system — dark theme, indigo/cyan palette.
"""

import streamlit as st


# ── Logo SVG ──────────────────────────────────────────────────────────────────

def logo_svg(size: int = 80) -> str:
    """Return the AI Testcase Generator neural-network logo as an inline SVG string."""
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="cg_{size}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#818cf8"/>
      <stop offset="100%" stop-color="#4f46e5"/>
    </radialGradient>
    <radialGradient id="ng_{size}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#67e8f9"/>
      <stop offset="100%" stop-color="#22d3ee"/>
    </radialGradient>
    <filter id="glow_{size}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Animated outer pulse rings -->
  <circle cx="50" cy="50" r="46" fill="none" stroke="#6366f1" stroke-width="0.6" opacity="0.3">
    <animate attributeName="opacity" values="0.3;0.07;0.3" dur="2.8s" repeatCount="indefinite"/>
    <animate attributeName="r"       values="43;47;43"       dur="2.8s" repeatCount="indefinite"/>
  </circle>
  <circle cx="50" cy="50" r="37" fill="none" stroke="#22d3ee" stroke-width="0.5" opacity="0.2">
    <animate attributeName="opacity" values="0.2;0.04;0.2" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="r"       values="35;39;35"       dur="2.2s" repeatCount="indefinite"/>
  </circle>

  <!-- Connection lines: center → outer nodes -->
  <line x1="50" y1="50" x2="18" y2="26" stroke="#6366f1" stroke-width="1.3" opacity="0.55"/>
  <line x1="50" y1="50" x2="82" y2="26" stroke="#6366f1" stroke-width="1.3" opacity="0.55"/>
  <line x1="50" y1="50" x2="18" y2="74" stroke="#6366f1" stroke-width="1.3" opacity="0.55"/>
  <line x1="50" y1="50" x2="82" y2="74" stroke="#6366f1" stroke-width="1.3" opacity="0.55"/>
  <line x1="50" y1="50" x2="50" y2="10" stroke="#a78bfa" stroke-width="1.3" opacity="0.45"/>
  <line x1="50" y1="50" x2="50" y2="90" stroke="#a78bfa" stroke-width="1.3" opacity="0.45"/>

  <!-- Cross-connections between outer nodes -->
  <line x1="18" y1="26" x2="50" y2="10" stroke="#22d3ee" stroke-width="0.7" opacity="0.28"/>
  <line x1="82" y1="26" x2="50" y2="10" stroke="#22d3ee" stroke-width="0.7" opacity="0.28"/>
  <line x1="18" y1="74" x2="50" y2="90" stroke="#22d3ee" stroke-width="0.7" opacity="0.28"/>
  <line x1="82" y1="74" x2="50" y2="90" stroke="#22d3ee" stroke-width="0.7" opacity="0.28"/>
  <line x1="18" y1="26" x2="18" y2="74" stroke="#22d3ee" stroke-width="0.7" opacity="0.15"/>
  <line x1="82" y1="26" x2="82" y2="74" stroke="#22d3ee" stroke-width="0.7" opacity="0.15"/>

  <!-- Corner nodes (cyan) -->
  <circle cx="18" cy="26" r="5.5" fill="url(#ng_{size})" filter="url(#glow_{size})"/>
  <circle cx="82" cy="26" r="5.5" fill="url(#ng_{size})" filter="url(#glow_{size})"/>
  <circle cx="18" cy="74" r="5.5" fill="url(#ng_{size})" filter="url(#glow_{size})"/>
  <circle cx="82" cy="74" r="5.5" fill="url(#ng_{size})" filter="url(#glow_{size})"/>

  <!-- Top / bottom nodes (violet) -->
  <circle cx="50" cy="10" r="4.5" fill="#a78bfa" filter="url(#glow_{size})"/>
  <circle cx="50" cy="90" r="4.5" fill="#a78bfa" filter="url(#glow_{size})"/>

  <!-- Center node (indigo) -->
  <circle cx="50" cy="50" r="15" fill="url(#cg_{size})" filter="url(#glow_{size})"/>

  <!-- Checkmark inside center node -->
  <path d="M42 51 L47.5 57.5 L60 43"
        stroke="white" stroke-width="2.8" fill="none"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


# ── Animation HTML snippets ───────────────────────────────────────────────────

def fetch_anim_html(ticket_key: str) -> str:
    """Animated card shown while fetching from Jira."""
    return f"""
<div class="anim-card">
  <div class="anim-radar">
    <div class="radar-sweep"></div>
    <svg width="24" height="24" viewBox="0 0 24 24"
         style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)">
      <path d="M12 2L12 6M12 18L12 22M2 12L6 12M18 12L22 12
               M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07
               M19.07 4.93L16.24 7.76M7.76 16.24L4.93 19.07"
            stroke="#6366f1" stroke-width="2" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="3.5" fill="#6366f1" opacity="0.9"/>
    </svg>
  </div>
  <div class="anim-text">
    <h4>Fetching&nbsp;<code style="background:rgba(99,102,241,0.2);color:#a78bfa;border-radius:4px;padding:2px 8px;font-size:0.88em">{ticket_key}</code>&nbsp;from Jira</h4>
    <p>Connecting to Jira API and retrieving ticket details…</p>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  </div>
</div>"""


def generate_anim_html(provider_label: str) -> str:
    """Animated card shown while the LLM generates test cases."""
    return f"""
<div class="anim-card">
  <div class="anim-neural">
    <svg width="26" height="26" viewBox="0 0 26 26"
         style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)">
      <circle cx="13" cy="13" r="4.5" fill="#22d3ee" opacity="0.9"/>
      <circle cx="5"  cy="6"  r="2"   fill="#67e8f9"/>
      <circle cx="21" cy="6"  r="2"   fill="#67e8f9"/>
      <circle cx="5"  cy="20" r="2"   fill="#67e8f9"/>
      <circle cx="21" cy="20" r="2"   fill="#67e8f9"/>
      <line x1="13" y1="13" x2="5"  y2="6"  stroke="#22d3ee" stroke-width="1" opacity="0.6"/>
      <line x1="13" y1="13" x2="21" y2="6"  stroke="#22d3ee" stroke-width="1" opacity="0.6"/>
      <line x1="13" y1="13" x2="5"  y2="20" stroke="#22d3ee" stroke-width="1" opacity="0.6"/>
      <line x1="13" y1="13" x2="21" y2="20" stroke="#22d3ee" stroke-width="1" opacity="0.6"/>
    </svg>
  </div>
  <div class="anim-text">
    <h4>Generating Test Cases</h4>
    <p>AI crafting comprehensive scenarios via&nbsp;<strong style="color:#22d3ee">{provider_label}</strong>…</p>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  </div>
</div>"""


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
/* ── Base ──────────────────────────────────────────────────────────────────── */
.stApp, .stApp > div {
  background-color: #0a0e1a !important;
}
[data-testid="stHeader"] {
  background: rgba(10,14,26,0.95) !important;
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(99,102,241,0.15);
}
[data-testid="stToolbar"] { display: none !important; }
.main .block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 3rem !important;
  max-width: 880px !important;
}

/* ── Scrollbar ──────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #111827; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6366f1; }

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(170deg, #0d1420 0%, #080c16 100%) !important;
  border-right: 1px solid rgba(99,102,241,0.18) !important;
}
[data-testid="stSidebar"] > div { background: transparent !important; }

/* ── Typography ─────────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, p, span, label, li { color: #e2e8f0; }
.stMarkdown p, .stMarkdown li  { color: #e2e8f0 !important; }
.stMarkdown h1, .stMarkdown h2,
.stMarkdown h3, .stMarkdown h4 { color: #e2e8f0 !important; }
[data-testid="stCaptionContainer"], .stCaption, small { color: #64748b !important; }

/* ── Code ───────────────────────────────────────────────────────────────────── */
code {
  background: rgba(99,102,241,0.15) !important;
  color: #a78bfa !important;
  border-radius: 4px !important;
  padding: 2px 6px !important;
  font-size: 0.85em !important;
}
pre {
  background: #1a2236 !important;
  border: 1px solid rgba(99,102,241,0.2) !important;
  border-radius: 10px !important;
}
pre code { background: transparent !important; color: #e2e8f0 !important; padding: 0 !important; }

/* ── HR ─────────────────────────────────────────────────────────────────────── */
hr { border-color: rgba(99,102,241,0.2) !important; }

/* ── Radio pills (provider selector) ───────────────────────────────────────── */
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div   { gap: 6px !important; flex-direction: column !important; }
[data-testid="stRadio"] label {
  background: #1a2236 !important;
  border: 1px solid rgba(99,102,241,0.28) !important;
  border-radius: 10px !important;
  padding: 9px 14px !important;
  color: #e2e8f0 !important;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex !important;
  align-items: center !important;
  margin: 0 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: #6366f1 !important;
  background: rgba(99,102,241,0.12) !important;
}
[data-testid="stRadio"] label span { color: #e2e8f0 !important; font-size: 0.875rem !important; }

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  font-size: 0.875rem !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25) !important;
}
.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Chip buttons (welcome screen) */
.st-key-chip1 button, .st-key-chip2 button, .st-key-chip3 button {
  background: #141e30 !important;
  border: 1px solid rgba(34,211,238,0.4) !important;
  color: #22d3ee !important;
  border-radius: 24px !important;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  padding: 5px 20px !important;
  box-shadow: none !important;
}
.st-key-chip1 button:hover,
.st-key-chip2 button:hover,
.st-key-chip3 button:hover {
  background: rgba(34,211,238,0.1) !important;
  box-shadow: 0 4px 14px rgba(34,211,238,0.2) !important;
  transform: translateY(-2px) !important;
}

/* Download button */
.stDownloadButton > button {
  background: transparent !important;
  color: #22d3ee !important;
  border: 1px solid rgba(34,211,238,0.4) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}
.stDownloadButton > button:hover {
  background: rgba(34,211,238,0.08) !important;
  box-shadow: 0 0 16px rgba(34,211,238,0.2) !important;
  transform: translateY(-1px) !important;
}

/* Form submit buttons */
[data-testid="stFormSubmitButton"] > button {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25) !important;
  transition: all 0.2s ease !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* ── Inputs ─────────────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"]  textarea,
.stTextInput input,
.stTextArea  textarea {
  background: #1a2236 !important;
  border: 1px solid rgba(99,102,241,0.28) !important;
  border-radius: 8px !important;
  color: #e2e8f0 !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"]  textarea:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
  outline: none !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"]  label { color: #94a3b8 !important; font-size: 0.82rem !important; }

[data-testid="stSelectbox"] > div > div {
  background: #1a2236 !important;
  border: 1px solid rgba(99,102,241,0.28) !important;
  border-radius: 8px !important;
  color: #e2e8f0 !important;
}

/* ── Chat input ─────────────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {
  background: rgba(10,14,26,0.9) !important;
  border-top: 1px solid rgba(99,102,241,0.2) !important;
  backdrop-filter: blur(8px);
  padding: 12px 16px !important;
}
[data-testid="stChatInputTextArea"] {
  background: #1a2236 !important;
  border: 1px solid rgba(99,102,241,0.28) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
  font-size: 0.9rem !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInputTextArea"]:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
[data-testid="stChatInputSubmitButton"] > button {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  border-radius: 8px !important;
  border: none !important;
}

/* ── Chat messages ──────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0.2rem 0 !important;
}
[data-testid="chatAvatarIcon-user"] {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
}
[data-testid="chatAvatarIcon-assistant"] {
  background: linear-gradient(135deg, #0e7490, #22d3ee) !important;
}

/* ── Expanders (test case cards) ────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background: #131d2e !important;
  border: 1px solid rgba(99,102,241,0.22) !important;
  border-radius: 12px !important;
  margin-bottom: 10px !important;
  overflow: hidden;
  animation: fadeSlideUp 0.38s ease;
  transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(99,102,241,0.55) !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.1);
}
[data-testid="stExpander"] details > summary {
  color: #e2e8f0 !important;
  font-weight: 600 !important;
  padding: 14px 18px !important;
  background: transparent !important;
  user-select: none;
}
[data-testid="stExpander"] details > summary:hover {
  background: rgba(99,102,241,0.07) !important;
}
[data-testid="stExpander"] details > div {
  border-top: 1px solid rgba(99,102,241,0.15) !important;
  padding: 14px 18px 16px !important;
  background: transparent !important;
}

/* ── Alerts ─────────────────────────────────────────────────────────────────── */
[data-testid="stSuccess"] {
  background: rgba(16,185,129,0.08) !important;
  border: 1px solid rgba(16,185,129,0.3) !important;
  border-radius: 10px !important;
  color: #6ee7b7 !important;
}
[data-testid="stError"] {
  background: rgba(239,68,68,0.08) !important;
  border: 1px solid rgba(239,68,68,0.3) !important;
  border-radius: 10px !important;
  color: #fca5a5 !important;
}
[data-testid="stWarning"] {
  background: rgba(245,158,11,0.08) !important;
  border: 1px solid rgba(245,158,11,0.3) !important;
  border-radius: 10px !important;
  color: #fcd34d !important;
}
[data-testid="stInfo"] {
  background: rgba(99,102,241,0.08) !important;
  border: 1px solid rgba(99,102,241,0.3) !important;
  border-radius: 10px !important;
}

/* ── Page link ──────────────────────────────────────────────────────────────── */
[data-testid="stPageLink"] a {
  color: #94a3b8 !important;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border-radius: 8px;
  transition: background 0.2s, color 0.2s;
  text-decoration: none !important;
}
[data-testid="stPageLink"] a:hover {
  background: rgba(99,102,241,0.1) !important;
  color: #e2e8f0 !important;
}

/* ── Animations ─────────────────────────────────────────────────────────────── */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes pulseRing {
  0%, 100% { transform: scale(1);    opacity: 0.55; }
  50%       { transform: scale(1.2); opacity: 0.04; }
}
@keyframes radarSweep {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes bounceDot {
  0%, 80%, 100% { transform: translateY(0);    opacity: 0.35; }
  40%           { transform: translateY(-7px); opacity: 1;    }
}
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}

/* ── Generation animation cards ─────────────────────────────────────────────── */
.anim-card {
  background: #131d2e;
  border: 1px solid rgba(99,102,241,0.28);
  border-radius: 14px;
  padding: 22px 26px;
  display: flex;
  align-items: center;
  gap: 22px;
  animation: fadeSlideUp 0.3s ease;
}
/* Radar (fetch) icon */
.anim-radar {
  width: 58px; height: 58px;
  border-radius: 50%;
  border: 2px solid #6366f1;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  position: relative;
  flex-shrink: 0;
}
.anim-radar::before {
  content: '';
  position: absolute; inset: -9px;
  border-radius: 50%;
  border: 1px solid rgba(99,102,241,0.3);
  animation: pulseRing 2s ease-in-out infinite;
}
.anim-radar::after {
  content: '';
  position: absolute; inset: -18px;
  border-radius: 50%;
  border: 1px solid rgba(99,102,241,0.14);
  animation: pulseRing 2s ease-in-out infinite 0.5s;
}
.radar-sweep {
  position: absolute; inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 290deg, rgba(99,102,241,0.75) 360deg);
  animation: radarSweep 1.6s linear infinite;
}
/* Neural (generate) icon */
.anim-neural {
  width: 58px; height: 58px;
  border-radius: 50%;
  border: 2px solid #22d3ee;
  background: radial-gradient(circle, rgba(34,211,238,0.12) 0%, transparent 70%);
  position: relative;
  flex-shrink: 0;
}
.anim-neural::before {
  content: '';
  position: absolute; inset: -9px;
  border-radius: 50%;
  border: 1px solid rgba(34,211,238,0.3);
  animation: pulseRing 1.8s ease-in-out infinite;
}
.anim-neural::after {
  content: '';
  position: absolute; inset: -18px;
  border-radius: 50%;
  border: 1px solid rgba(34,211,238,0.13);
  animation: pulseRing 1.8s ease-in-out infinite 0.45s;
}
/* Text area in animation cards */
.anim-text h4 {
  margin: 0 0 5px !important;
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  color: #e2e8f0 !important;
}
.anim-text p {
  margin: 0 !important;
  font-size: 0.82rem !important;
  color: #64748b !important;
  line-height: 1.5 !important;
}
/* Animated typing dots */
.typing-dots {
  display: inline-flex;
  gap: 5px;
  margin-top: 9px;
  align-items: center;
}
.typing-dots span {
  width: 7px; height: 7px;
  border-radius: 50%;
  display: inline-block;
  animation: bounceDot 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(1) { background: #6366f1; }
.typing-dots span:nth-child(2) { background: #a78bfa; animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { background: #22d3ee; animation-delay: 0.30s; }

/* ── Welcome hero ───────────────────────────────────────────────────────────── */
.welcome-hero {
  text-align: center;
  padding: 2.5rem 1rem 1rem;
  animation: fadeSlideUp 0.5s ease;
}
.welcome-hero h2 {
  font-size: 1.85rem !important;
  font-weight: 800 !important;
  background: linear-gradient(135deg, #818cf8, #22d3ee) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  margin: 0.8rem 0 0.4rem !important;
  display: inline-block !important;
  letter-spacing: -0.02em !important;
}
.welcome-hero p {
  color: #64748b !important;
  font-size: 0.95rem !important;
  margin-bottom: 0 !important;
  line-height: 1.6 !important;
}
.welcome-divider {
  width: 64px; height: 3px;
  background: linear-gradient(90deg, #6366f1, #22d3ee);
  border-radius: 2px;
  margin: 1.1rem auto 1.3rem;
}
.chip-hint {
  font-size: 0.78rem !important;
  color: #64748b !important;
  margin-bottom: 0.65rem !important;
  letter-spacing: 0.03em !important;
  text-transform: uppercase !important;
}

/* ── Test-case section header ────────────────────────────────────────────────── */
.tc-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0 12px;
  border-bottom: 1px solid rgba(99,102,241,0.18);
  margin-bottom: 14px;
  animation: fadeSlideUp 0.3s ease;
}
.tc-section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #e2e8f0 !important;
}
.tc-badge {
  background: rgba(99,102,241,0.15);
  color: #a78bfa;
  border: 1px solid rgba(99,102,241,0.3);
  border-radius: 20px;
  padding: 3px 13px;
  font-size: 0.73rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* ── Sidebar logo wrapper ────────────────────────────────────────────────────── */
.logo-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.3rem 0 1.1rem;
}
.logo-glow { filter: drop-shadow(0 0 14px rgba(99,102,241,0.45)); }
.brand-name {
  background: linear-gradient(135deg, #818cf8, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 1.28rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-top: 10px;
  display: inline-block;
}
.brand-sub {
  color: #475569;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-top: 3px;
}
.provider-label {
  font-size: 0.72rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
  margin-bottom: 8px;
  padding-left: 2px;
}

/* ── Page header ────────────────────────────────────────────────────────────── */
.page-hdr {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(99,102,241,0.18);
  margin-bottom: 20px;
  animation: fadeSlideUp 0.4s ease;
}
.page-hdr-title {
  font-size: 1.55rem;
  font-weight: 800;
  background: linear-gradient(135deg, #818cf8, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  display: inline-block;
  letter-spacing: -0.02em;
}
.page-hdr-sub {
  font-size: 0.8rem;
  color: #64748b !important;
  margin: 3px 0 0 !important;
  line-height: 1.5;
}

/* ── Settings cards ─────────────────────────────────────────────────────────── */
.sc {
  background: #111827;
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 14px;
  padding: 20px 22px;
  margin-bottom: 14px;
  animation: fadeSlideUp 0.4s ease;
  transition: border-color 0.2s;
}
.sc:hover { border-color: rgba(99,102,241,0.4); }
.sc-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.sc-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 7px;
}
.status-pill {
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 20px;
  padding: 3px 11px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.status-pill::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-pill.connected {
  background: rgba(16,185,129,0.12);
  color: #34d399;
  border: 1px solid rgba(16,185,129,0.3);
}
.status-pill.connected::before { background: #34d399; box-shadow: 0 0 5px #34d399; }
.status-pill.failed {
  background: rgba(239,68,68,0.12);
  color: #f87171;
  border: 1px solid rgba(239,68,68,0.3);
}
.status-pill.failed::before { background: #f87171; }
.status-pill.untested {
  background: rgba(100,116,139,0.12);
  color: #94a3b8;
  border: 1px solid rgba(100,116,139,0.25);
}
.status-pill.untested::before { background: #64748b; }

/* ── Test-case table ─────────────────────────────────────────────────────────── */
.tc-table-wrap {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid rgba(99,102,241,0.25);
  margin-bottom: 16px;
  animation: fadeSlideUp 0.38s ease;
}
.tc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  background: #111827;
}
.tc-table thead tr {
  background: linear-gradient(135deg, rgba(99,102,241,0.22), rgba(34,211,238,0.1));
  border-bottom: 2px solid rgba(99,102,241,0.3);
}
.tc-table th {
  padding: 13px 16px;
  text-align: left;
  font-size: 0.71rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #a78bfa;
  white-space: nowrap;
}
.th-id    { width: 80px; }
.th-desc  { width: 230px; }
.th-steps { min-width: 280px; }
.th-outcome { width: 210px; }

.tc-table tbody tr {
  border-bottom: 1px solid rgba(99,102,241,0.1);
  transition: background 0.15s;
}
.tc-table tbody tr:last-child { border-bottom: none; }
.tc-table tbody tr:hover { background: rgba(99,102,241,0.05); }
.tc-table td {
  padding: 14px 16px;
  vertical-align: top;
  color: #e2e8f0;
}

/* ID cell */
.tc-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99,102,241,0.22), rgba(79,70,229,0.12));
  border: 1px solid rgba(99,102,241,0.4);
  color: #a78bfa;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 5px 10px;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  white-space: nowrap;
}

/* Description cell */
.tc-ttl {
  font-weight: 700;
  color: #e2e8f0;
  font-size: 0.875rem;
  margin-bottom: 5px;
  line-height: 1.4;
}
.tc-sum {
  color: #94a3b8;
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 5px;
}
.tc-pre {
  font-size: 0.75rem;
  color: #64748b;
  background: rgba(99,102,241,0.07);
  border-left: 2px solid rgba(99,102,241,0.4);
  padding: 4px 8px;
  border-radius: 0 4px 4px 0;
  line-height: 1.4;
  margin-top: 4px;
}
.tc-pre-lbl {
  color: #a78bfa;
  font-weight: 600;
  margin-right: 4px;
}

/* Steps cell */
.step-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 7px 0;
  border-bottom: 1px solid rgba(99,102,241,0.07);
}
.step-item:first-child { padding-top: 0; }
.step-item:last-child  { border-bottom: none; padding-bottom: 0; }
.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  background: rgba(34,211,238,0.12);
  border: 1px solid rgba(34,211,238,0.3);
  color: #22d3ee;
  border-radius: 50%;
  font-size: 0.68rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}
.step-body { flex: 1; min-width: 0; }
.step-action {
  color: #e2e8f0;
  font-size: 0.82rem;
  line-height: 1.45;
}
.step-data {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #94a3b8;
  background: rgba(34,211,238,0.06);
  border-left: 2px solid rgba(34,211,238,0.35);
  padding: 3px 8px;
  border-radius: 0 4px 4px 0;
  line-height: 1.4;
}
.step-data-lbl {
  color: #22d3ee;
  font-weight: 600;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 4px;
}

/* Expected outcome cell */
.td-outcome {
  color: #e2e8f0 !important;
  font-size: 0.82rem !important;
  line-height: 1.55 !important;
}
.no-steps { color: #475569; font-style: italic; }
</style>
"""


def inject_styles() -> None:
    """Inject all Neural Test Lab styles into the active Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
