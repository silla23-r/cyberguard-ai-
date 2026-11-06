"""
Deterministic Hybrid Risk Scoring and Verdict Engine for CyberGuard AI.
Combines empirical threat intelligence, cryptographic/syntax validations,
and psychological coercion signals into an explainable 0-100 threat score.
"""
import logging
from typing import List, Optional

from models.schemas import (
    ForensicEvidence,
    ThreatIntelligence,
    CoercionAnalysis,
    RiskVerdict,
    ScamArchetype
)

logger = logging.getLogger(__name__)

def calculate_verdict(
    evidence: ForensicEvidence,
    threat_intel: ThreatIntelligence,
    coercion: Optional[CoercionAnalysis] = None,
    user_language: str = "en"
) -> RiskVerdict:
    """
    Computes a deterministic threat score (0-100) with full evidentiary justification.
    """
    score = 0
    reasoning: List[str] = []
    archetype = ScamArchetype.UNKNOWN_SUSPICIOUS

    # 1. Threat Intelligence URL & Domain Checks
    if threat_intel.virustotal_malicious_count > 0:
        points = min(40, threat_intel.virustotal_malicious_count * 10)
        score += points
        reasoning.append(f"🚨 Known Threat: Flagged as malicious by {threat_intel.virustotal_malicious_count} antivirus vendor(s) on VirusTotal (+{points} pts).")

    if threat_intel.is_blacklisted_domain:
        score += 30
        reasoning.append("🚨 Blacklist Match: Destination domain appears on Google Safe Browsing / Phishing registries (+30 pts).")

    if threat_intel.is_domain_suspicious and threat_intel.domain_age_days is not None:
        score += 25
        reasoning.append(f"⚠️ Brand New Domain: Web domain was created only {threat_intel.domain_age_days} days ago. Legitimate banks and utilities never operate on freshly registered domains (+25 pts).")

    # 1B. Heuristic Phishing & Spoofed URL Patterns
    suspicious_tlds = [".xyz", ".top", ".site", ".live", ".buzz", ".online", ".guru", ".link", ".cc"]
    phishing_keywords = ["verify", "kyc", "update", "secure", "login", "reward", "freemoney", "free-recharge", "apk", "task", "bonus"]
    
    for url in evidence.extracted_urls:
        u_lower = url.lower()
        has_tld = any(u_lower.endswith(t) or f"{t}/" in u_lower for t in suspicious_tlds)
        has_keyword = any(k in u_lower for k in phishing_keywords)
        is_apk = u_lower.endswith(".apk") or ".apk?" in u_lower

        if is_apk:
            score += 45
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"🚨 Dangerous APK Download: The link directs to an unverified Android package (.apk), which commonly installs banking trojans or spyware (+45 pts).")
            break
        elif (has_tld or has_keyword) and evidence.impersonated_brand:
            score += 35
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"🚨 Phishing URL Flagged: The link uses an unofficial domain/path containing high-risk credential-harvesting keywords (+35 pts).")
            break
        elif has_tld and has_keyword:
            score += 30
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"⚠️ Suspicious Web Link: The URL contains deceptive keywords paired with an unusual domain extension (+30 pts).")
            break

    # 2. UPI & QR Code Transaction Forensic Checks
    if evidence.qr_parsed:
        qr_type = evidence.qr_parsed.get("type")
        if qr_type == "UPI_PAYMENT":
            upi = evidence.qr_parsed.get("upi_details", {})
            if upi.get("is_collect_request"):
                score += 45
                archetype = ScamArchetype.UPI_COLLECT_FRAUD
                reasoning.append("🛑 UPI Collect Fraud: The QR code is programmed to DEBIT/COLLECT money from your bank account, not credit money to you (+45 pts).")
            
            if upi.get("amount") and float(upi.get("amount") or 0) > 0:
                score += 15
                reasoning.append(f"⚠️ Pre-filled Deduction: QR initiates an immediate debit authorization for ₹{upi.get('amount')} (+15 pts).")
        elif qr_type == "WEB_URL":
            qr_url = (evidence.qr_parsed.get("url") or "").lower()
            if any(t in qr_url for t in suspicious_tlds) or any(k in qr_url for k in phishing_keywords):
                score += 40
                archetype = ScamArchetype.PHISHING_LINK
                reasoning.append("🚨 Concealed QR Phishing (Quishing): Embedded QR code payload redirects to an unofficial credential-harvesting domain (+40 pts).")

    if threat_intel.upi_vpa_suspicious:
        score += 25
        archetype = ScamArchetype.UPI_COLLECT_FRAUD
        for r in threat_intel.upi_vpa_reasons:
            reasoning.append(f"⚠️ Suspicious VPA: {r} (+25 pts).")

    # 3. Brand Impersonation Checks
    if evidence.impersonated_brand:
        score += 20
        reasoning.append(f"⚠️ Impersonation Detected: Visual or textual mimicry of '{evidence.impersonated_brand}' detected (+20 pts).")

    # 4. Psychological Coercion & Social Engineering Checks
    if coercion and coercion.coercion_score > 0:
        added_pts = int(coercion.coercion_score * 0.3)
        score += added_pts
        reasoning.append(f"⚠️ Psychological Pressure: Strong extortion / urgency tactics detected (+{added_pts} pts).")
        
        # Check for Digital Arrest or Utility Disconnection signatures
        for tactic in coercion.tactics_detected:
            reasoning.append(f"   • {tactic}")
            if "arrest" in tactic.lower() or "cbi" in tactic.lower() or "police" in tactic.lower():
                archetype = ScamArchetype.DIGITAL_ARREST
            elif "electricity" in tactic.lower() or "power" in tactic.lower():
                archetype = ScamArchetype.FAKE_ELECTRICITY_BILL

    if evidence.urgency_signals:
        score += 10
        reasoning.append(f"⚠️ Artificial Urgency: Identified {len(evidence.urgency_signals)} high-pressure phrases designed to prevent rational thinking (+10 pts).")

    # 5. Steganography & Concealed Data Checks
    if any("steganography" in u.lower() for u in evidence.urgency_signals):
        score += 40
        reasoning.append("🚨 Pixel Steganography Unmasked: Hidden payload was extracted from the image's Least Significant Bits (+40 pts).")
        if archetype == ScamArchetype.UNKNOWN_SUSPICIOUS:
            archetype = ScamArchetype.PHISHING_LINK

    # Cap final risk score at 100
    final_score = min(100, max(0, score))

    # Determine Severity Tier
    if final_score >= 65:
        severity = "DANGER"
    elif final_score >= 30:
        severity = "CAUTION"
    else:
        severity = "SAFE"
        if not reasoning:
            reasoning.append("✅ No known phishing signatures, brand spoofing, or fraudulent QR triggers detected.")
            archetype = ScamArchetype.LEGITIMATE_SAFE

    # Refine Archetype if still unknown or specific
    raw_lower = (evidence.raw_text or "").lower()
    if "kyc" in raw_lower and ("suspend" in raw_lower or "block" in raw_lower or "bank" in raw_lower):
        if final_score >= 35:
            archetype = ScamArchetype.BANK_KYC_SUSPENSION
    elif archetype == ScamArchetype.UNKNOWN_SUSPICIOUS:
        if evidence.extracted_urls and final_score >= 40:
            archetype = ScamArchetype.PHISHING_LINK
        elif evidence.impersonated_brand and "electricity" in (evidence.impersonated_brand or "").lower():
            archetype = ScamArchetype.FAKE_ELECTRICITY_BILL
        elif final_score < 30:
            archetype = ScamArchetype.LEGITIMATE_SAFE

    # Multilingual Localization Dictionaries
    LANG_DATA = {
        "hi": {
            "DANGER": (
                f"🛑 आगे न बढ़ें! यह एक गंभीर और पुख्ता धोखाधड़ी ({archetype.value.replace('_', ' ')}) है। "
                "इस QR कोड को स्कैन न करें, किसी लिंक पर क्लिक न करें और कोई पैसा न भेजें। "
                "पुलिस, बैंक या बिजली विभाग कभी भी वीडियो कॉल पर गिरफ़्तारी की धमकी नहीं देते और न ही तत्काल UPI ट्रांसफर मांगते हैं।",
                [
                    "व्हाट्सएप / SMS पर भेजने वाले का नंबर तुरंत ब्लॉक और रिपोर्ट करें।",
                    "अपना UPI PIN कभी दर्ज न करें। याद रखें: पैसे प्राप्त करने के लिए PIN की आवश्यकता कभी नहीं होती।",
                    "यदि आपने पैसे भेज दिए हैं, तो तुरंत राष्ट्रीय साइबर अपराध हेल्पलाइन 1930 पर कॉल करें।",
                    "आधिकारिक पोर्टल cybercrime.gov.in पर साक्ष्य के साथ शिकायत दर्ज करें।"
                ]
            ),
            "CAUTION": (
                "⚠️ सावधानी बरतें! हमें संदिग्ध संकेत मिले हैं जैसे असत्यापित प्रेषक या हाल ही में बनाया गया वेब डोमेन। सीधे आधिकारिक वेबसाइट या बैंक ऐप से पुष्टि करें।",
                [
                    "SMS या व्हाट्सएप पर आए लिंक पर क्लिक न करें। स्वयं ब्राउज़र में आधिकारिक वेबसाइट खोलें।",
                    "वेबसाइट स्पेलिंग को ध्यान से जांचें (जैसे sbi.co.in के बजाय नकली लिंक)।",
                    "OTP, पासवर्ड किसी से साझा न करें और AnyDesk या TeamViewer जैसे ऐप इंस्टॉल न करें।"
                ]
            ),
            "SAFE": (
                "✅ कोई खतरा नहीं मिला। यह संदेश या QR ज्ञात धोखाधड़ी संकेतों से मुक्त प्रतीत होता है।",
                [
                    "लेन-देन की पुष्टि करने से पहले हमेशा राशि और प्राप्तकर्ता का नाम सत्यापित करें।",
                    "याद रखें कि प्रामाणिक संस्थाएं कभी भी आपके गोपनीय बैंकिंग क्रेडेंशियल नहीं मांगती हैं।"
                ]
            )
        },
        "te": {
            "DANGER": (
                f"🛑 ముందుకు సాగవద్దు! ఇది నిర్ధారించబడిన తీవ్రమైన సైబర్ మోసం ({archetype.value.replace('_', ' ')}). "
                "ఈ QR కోడ్‌ను స్కాన్ చేయవద్దు, లింక్‌లను క్లిక్ చేయవద్దు మరియు ఎవరికీ డబ్బు పంపవద్దు. "
                "పోలీసులు, బ్యాంకులు లేదా విద్యుత్ శాఖ అధికారులు వీడియో కాల్స్‌లో అరెస్ట్ చేస్తామని ఎప్పుడూ బెదిరించరు, తక్షణ UPI చెల్లింపులు అడగరు.",
                [
                    "సందేశం పంపిన నంబర్‌ను వాట్సాప్ / SMS లో వెంటనే బ్లాక్ చేసి రిపోర్ట్ చేయండి.",
                    "మీ UPI పిన్ ఎప్పటికీ నమోదు చేయవద్దు. గుర్తుంచుకోండి: డబ్బు అందుకోవడానికి పిన్ అవసరం లేదు.",
                    "మీరు ఇప్పటికే డబ్బు పంపి ఉంటే, వెంటనే జాతీయ సైబర్ క్రైమ్ హెల్ప్‌లైన్ 1930 కి కాల్ చేయండి.",
                    "అధికారిక పోర్టల్ cybercrime.gov.in లో ఆధారాలతో ఫిర్యాదు నమోదు చేయండి."
                ]
            ),
            "CAUTION": (
                "⚠️ జాగ్రత్తగా ఉండండి! నమోదు చేయని పంపినవారు లేదా కొత్త వెబ్‌సైట్ లింక్‌లు వంటి అనుమానాస్పద అంశాలు గుర్తించబడ్డాయి. అధికారిక యాప్ లేదా వెబ్‌సైట్ ద్వారా ధృవీకరించుకోండి.",
                [
                    "SMS లేదా వాట్సాప్‌లోని లింక్‌లపై క్లిక్ చేయవద్దు. బ్రౌజర్‌లో అధికారిక వెబ్‌సైట్‌ను స్వయంగా తెరవండి.",
                    "స్పెల్లింగ్ లోపాలు ఉన్నాయేమో జాగ్రత్తగా పరిశీలించండి.",
                    "OTP లేదా పాస్‌వర్డ్‌లను ఎవరితోనూ పంచుకోవద్దు మరియు AnyDesk వంటి యాప్‌లను ఇన్‌స్టాల్ చేయవద్దు."
                ]
            ),
            "SAFE": (
                "✅ ఎటువంటి ముప్పు కనుగొనబడలేదు. ఇది సురక్షితంగా ఉన్నట్లు కనిపిస్తోంది.",
                [
                    "చెల్లింపు ధృవీకరించే ముందు ఎల్లప్పుడూ మొత్తం మరియు పేరును సరిచూసుకోండి.",
                    "అసలైన సంస్థలు మీ బ్యాంకింగ్ వివరాలు లేదా రహస్య సమాచారాన్ని ఎప్పటికీ అడగవు."
                ]
            )
        },
        "ta": {
            "DANGER": (
                f"🛑 தொடர வேண்டாம்! இது மிக அதிக ஆபத்துள்ள நிதி மோசடி ({archetype.value.replace('_', ' ')}). "
                "இந்த QR குறியீட்டை ஸ்கேன் செய்யாதீர்கள், இணைப்புகளைக் கிளிக் செய்யாதீர்கள், பணம் அனுப்பாதீர்கள். "
                "காவல்துறை, வங்கிகள் அல்லது மின்சார வாரியங்கள் வீடியோ காலில் கைது செய்ய அச்சுறுத்தவோ, அவசர UPI பணம் கேட்கவோ மாட்டார்கள்.",
                [
                    "வாட்ஸ்அப் அல்லது SMS இல் அனுப்பிய எண்ணை உடனடியாக பிளாக் செய்து புகார் அளிக்கவும்.",
                    "உங்கள் UPI பின் எண்ணை உள்ளிட வேண்டாம். நினைவில் கொள்ளுங்கள்: பணம் பெற PIN தேவையில்லை.",
                    "ஏற்கனவே பணம் அனுப்பியிருந்தால், உடனடியாக தேசிய சைபர் கிரைம் உதவி எண் 1930 ஐ அழைக்கவும்.",
                    "cybercrime.gov.in என்ற அதிகாரப்பூர்வ போர்ட்டலில் சான்றுகளுடன் புகார் பதிவு செய்யவும்."
                ]
            ),
            "CAUTION": (
                "⚠️ எச்சரிக்கையுடன் செயல்படுங்கள்! சரிபார்க்கப்படாத அனுப்புநர் போன்ற சந்தேகத்திற்குரிய அறிகுறிகள் கண்டறியப்பட்டுள்ளன. அதிகாரப்பூர்வ வலைத்தளம் மூலம் சரிபார்க்கவும்.",
                [
                    "SMS அல்லது வாட்ஸ்அப் வழியாக வந்த இணைப்புகளைக் கிளிக் செய்யாதீர்கள். உலாவியில் முகவரியை நேரடியாக தட்டச்சு செய்யவும்.",
                    "வலைத்தள முகவரியை கவனமாக சரிபார்க்கவும்.",
                    "OTP, கடவுச்சொற்களைப் பகிர வேண்டாம், AnyDesk போன்ற செயலிகளை நிறுவ வேண்டாம்."
                ]
            ),
            "SAFE": (
                "✅ எந்த அச்சுறுத்தலும் கண்டறியப்படவில்லை. இது பாதுகாப்பானதாகத் தோன்றுகிறது.",
                [
                    "பரிவர்த்தனையை உறுதிப்படுத்தும் முன் தொகையையும் பெறுநர் பெயரையும் எப்போதும் சரிபார்க்கவும்.",
                    "அங்கீகரிக்கப்பட்ட நிறுவனங்கள் உங்கள் வங்கி ரகசியங்களை ஒருபோதும் கேட்காது என்பதை நினைவில் கொள்க."
                ]
            )
        },
        "bn": {
            "DANGER": (
                f"🛑 এগিয়ে যাবেন না! এটি একটি অত্যন্ত বিপজ্জনক সাইবার প্রতারণা ({archetype.value.replace('_', ' ')}). "
                "এই QR কোডটি স্ক্যান করবেন না, কোনো লিঙ্কে ক্লিক করবেন না এবং কোনো টাকা পাঠাবেন না। "
                "পুলিশ, ব্যাঙ্ক বা বিদ্যুৎ দপ্তর কখনোই ভিডিও কলে গ্রেফতারের হুমকি দেয় না বা তৎক্ষণাৎ UPI ট্রান্সফার দাবি করে না।",
                [
                    "হোয়াটসঅ্যাপ বা SMS-এ প্রেরকের নম্বরটি অবিলম্বে ব্লক ও রিপোর্ট করুন।",
                    "কখনোই আপনার UPI PIN প্রবেশ করাবেন না। মনে রাখবেন: টাকা পাওয়ার জন্য PIN লাগে না।",
                    "টাকা পাঠিয়ে থাকলে অবিলম্বে জাতীয় সাইবার ক্রাইম হেল্পলাইন ১৯৩০-এ কল করুন।",
                    "সরকারি পোর্টাল cybercrime.gov.in-এ প্রমাণের সাথে অভিযোগ নথিভুক্ত করুন।"
                ]
            ),
            "CAUTION": (
                "⚠️ সতর্ক থাকুন! সন্দেহজনক সংকেত যেমন অজানা প্রেরক বা নতুন ওয়েব লিঙ্ক শনাক্ত করা হয়েছে। সরাসরি অফিসিয়াল ওয়েবসাইট থেকে যাচাই করুন।",
                [
                    "SMS বা হোয়াটসঅ্যাপের লিঙ্কে ক্লিক করবেন না। ব্রাউজারে অফিসিয়াল ঠিকানা নিজে টাইপ করুন।",
                    "বানান ভুল বা ভুয়ো লিঙ্ক ভালো করে লক্ষ্য করুন।",
                    "কাউকে OTP বা পাসওয়ার্ড দেবেন না এবং AnyDesk বা TeamViewer ইনস্টল করবেন না।"
                ]
            ),
            "SAFE": (
                "✅ কোনো বিপদ পাওয়া যায়নি। এই বার্তাটিতে পরিচিত কোনো প্রতারণার লক্ষণ নেই।",
                [
                    "লেনদেনের আগে সর্বদা প্রাপকের নাম ও টাকার পরিমাণ যাচাই করুন।",
                    "মনে রাখবেন আসল সংস্থা কখনোই আপনার গোপন পাসওয়ার্ড বা পিন চাইবে না।"
                ]
            )
        }
    }

    # Generate Plain-Language Advisory & Immediate Action Checklist (Default: English)
    if severity == "DANGER":
        advisory = (
            f"🛑 DO NOT PROCEED. This is a high-confidence {archetype.value.replace('_', ' ')}. "
            "Do NOT scan this QR code, do NOT click the link, and do NOT send money. "
            "Official organizations (police, banks, electricity boards) NEVER demand immediate UPI transfers "
            "or threaten arrest over video calls."
        )
        checklist = [
            "Block and report the sender's phone number on WhatsApp / SMS immediately.",
            "Never enter your UPI PIN. Remember: You NEVER need to enter your PIN to receive money.",
            "If you have already sent money, immediately call the National Cyber Crime Helpline at 1930.",
            "Report the fraud with evidence on the official portal: cybercrime.gov.in."
        ]
    elif severity == "CAUTION":
        advisory = (
            "⚠️ PROCEED WITH CAUTION. We detected suspicious indicators such as a recently created web domain "
            "or unverified sender handle. Verify directly through the official website or verified mobile app."
        )
        checklist = [
            "Do not click links received via SMS/WhatsApp. Open your browser and type the official URL yourself.",
            "Check the URL carefully for subtle spelling mistakes (e.g. sbi-kyc-update.com instead of sbi.co.in).",
            "Never share OTPs, passwords, or install remote assistance apps like AnyDesk or TeamViewer."
        ]
    else:
        advisory = "✅ NO THREATS DETECTED. This communication appears clean of known fraud indicators."
        checklist = [
            "Always verify payment amounts and recipient names before confirming transactions.",
            "Remember that genuine organizations will never ask for your confidential banking credentials."
        ]

    # Override with regional translation if requested
    target_lang = (user_language or "en").lower().strip()
    if target_lang in LANG_DATA and severity in LANG_DATA[target_lang]:
        advisory, checklist = LANG_DATA[target_lang][severity]

    confidence = 0.95 if final_score > 70 or final_score < 20 else 0.82

    return RiskVerdict(
        risk_score=final_score,
        severity=severity,
        confidence=confidence,
        scam_archetype=archetype,
        reasoning=reasoning,
        actionable_advisory=advisory,
        safety_checklist=checklist
    )

