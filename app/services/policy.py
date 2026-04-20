from dataclasses import dataclass
from typing import Literal

PolicyDecision = Literal["allow", "staff_handoff", "safe_fallback"]

_STAFF_KEYWORDS = ["スタッフ", "店員", "呼んで", "来て"]

_MEDICAL_KEYWORDS = [
    "治る", "治す", "薬", "診断", "処方", "症状", "病気",
    "アレルギー", "副作用", "服用", "飲めば",
]
_LEGAL_KEYWORDS = [
    "訴える", "裁判", "違法", "法律", "弁護士", "賠償",
    "契約違反", "損害",
]
_DANGEROUS_KEYWORDS = [
    "殺す", "死ね", "爆破", "毒", "武器", "犯罪",
]
_PII_KEYWORDS = [
    "住所を教えて", "電話番号を教えて", "個人情報",
    "クレジットカード", "マイナンバー",
]

_UNSAFE_ANSWER_KEYWORDS = _MEDICAL_KEYWORDS + _LEGAL_KEYWORDS + _DANGEROUS_KEYWORDS

_MEDICAL_ASSERTIONS = [
    "治ります", "効きます", "飲んでください", "服用してください",
    "大丈夫です",
]
_LEGAL_ASSERTIONS = [
    "違法です", "合法です", "問題ありません", "訴えることができます",
]


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str = ""


class PolicyService:
    def precheck(self, question: str) -> PolicyResult:
        for kw in _STAFF_KEYWORDS:
            if kw in question:
                return PolicyResult(decision="staff_handoff", reason="customer_requested_staff")

        for kw in _DANGEROUS_KEYWORDS:
            if kw in question:
                return PolicyResult(decision="safe_fallback", reason="dangerous_content")

        for kw in _PII_KEYWORDS:
            if kw in question:
                return PolicyResult(decision="safe_fallback", reason="pii_request")

        for kw in _MEDICAL_KEYWORDS:
            if kw in question:
                return PolicyResult(decision="safe_fallback", reason="medical_advice_request")

        for kw in _LEGAL_KEYWORDS:
            if kw in question:
                return PolicyResult(decision="safe_fallback", reason="legal_advice_request")

        return PolicyResult(decision="allow")

    def final_check(self, answer: str) -> PolicyResult:
        for phrase in _MEDICAL_ASSERTIONS:
            if phrase in answer:
                return PolicyResult(decision="safe_fallback", reason="medical_assertion_in_answer")

        for phrase in _LEGAL_ASSERTIONS:
            if phrase in answer:
                return PolicyResult(decision="safe_fallback", reason="legal_assertion_in_answer")

        for kw in _DANGEROUS_KEYWORDS:
            if kw in answer:
                return PolicyResult(decision="safe_fallback", reason="dangerous_content_in_answer")

        return PolicyResult(decision="allow")
