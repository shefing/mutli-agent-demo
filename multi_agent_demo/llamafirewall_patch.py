"""
Runtime patch for LlamaFirewall's AlignmentCheck scanner model.

LlamaFirewall's AlignmentCheckScanner hardcodes its model to
``meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`` and exposes no
constructor argument or environment variable to override it. Together AI
retired that model from its serverless tier, so every AlignmentCheck call now
returns HTTP 400 ``model_not_available`` (the scanner swallows the error and
emits a meaningless default BLOCK).

This module monkeypatches ``AlignmentCheckScanner.__init__`` to pass a
serverless model into the parent ``CustomCheckScanner``. Import it once, before
any ``LlamaFirewall(...)`` is constructed.

Override the model with the ALIGNMENT_MODEL env var if Together's serverless
catalog changes again.
"""

import os

# Confirmed serverless on Together AI (chat completions). Override via env if needed.
ALIGNMENT_MODEL = os.getenv(
    "ALIGNMENT_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo"
)

_patched = False


def apply_alignment_model_patch() -> None:
    """Force AlignmentCheckScanner to use a serverless Together model. Idempotent."""
    global _patched
    if _patched:
        return

    from llamafirewall.scanners.custom_check_scanner import CustomCheckScanner
    from llamafirewall.scanners.experimental import alignmentcheck_scanner as acs

    _orig_init = acs.AlignmentCheckScanner.__init__

    def _patched_init(self, scanner_name: str = "AlignmentCheck Scanner") -> None:
        CustomCheckScanner.__init__(
            self,
            scanner_name=scanner_name,
            system_prompt=acs.SYSTEM_PROMPT,
            output_schema=acs.AlignmentCheckOutputSchema,
            model_name=ALIGNMENT_MODEL,
        )
        self.require_full_trace = True

    acs.AlignmentCheckScanner.__init__ = _patched_init
    _patched = True
    print(f"🔧 AlignmentCheck model patched to serverless: {ALIGNMENT_MODEL}")


# Apply on import so a simple `import multi_agent_demo.llamafirewall_patch` is enough.
apply_alignment_model_patch()
