export type SupportedLanguage = "en" | "hi" | "te" | "ta" | "bn";

export interface TranslationDict {
  header: {
    subtitle: string;
    helpline: string;
  };
  hero: {
    badge: string;
    title1: string;
    titleHighlight: string;
    title2: string;
    desc: string;
    badgeOcr: string;
    badgeQr: string;
    badgeAudio: string;
  };
  upload: {
    tabImage: string;
    tabAudio: string;
    tabText: string;
    tabWhatsapp: string;
    dropImagePrompt: string;
    dropImageHint: string;
    dropAudioPrompt: string;
    dropAudioHint: string;
    pastePlaceholder: string;
    scanButton: string;
    scanningButton: string;
    changeFile: string;
    waTitle: string;
    waSubtitle: string;
    waPresetsLabel: string;
    waPresetKyc: string;
    waPresetElectricity: string;
    waPresetArrest: string;
    waPlaceholder: string;
    waSendBtn: string;
    waAnalyzingBtn: string;
    waBlockedBadge: string;
    waBlockBtn: string;
    waBlockingBtn: string;
    waSafeBadge: string;
    waDangerBadge: string;
  };
  threat: {
    riskScoreLabel: string;
    downloadReport: string;
    generatingPdf: string;
    listenAdvisory: string;
    playingAudio: string;
    advisoryHeading: string;
  };
  actions: {
    actionsHeading: string;
    emergencyHeading: string;
    emergencySub: string;
    dialHelpline: string;
    nationalPortal: string;
  };
  evidence: {
    evidenceHeading: string;
    noEvidence: string;
    detectedBrand: string;
    urlAnalysis: string;
    upiAnalysis: string;
    audioAnalysis: string;
    flags: string;
  };
  footer: {
    desc: string;
    legal: string;
  };
}

export const translations: Record<SupportedLanguage, TranslationDict> = {
  en: {
    header: {
      subtitle: "Multimodal Fraud & Scam Defense",
      helpline: "1930 Helpline",
    },
    hero: {
      badge: "Protecting Citizens Against Financial Extortion",
      title1: "Never Fall for a ",
      titleHighlight: "Digital Arrest or UPI Scam",
      title2: " Again.",
      desc: "Upload a suspicious screenshot, scan a payment QR code, or upload a threatening call recording. Our multi-agent AI verifies registries in real time and compiles an official cybercrime report.",
      badgeOcr: "Screenshot OCR",
      badgeQr: "UPI Collect QR Decoder",
      badgeAudio: "Call Threat Acoustic Analysis",
    },
    upload: {
      tabImage: "Screenshot / QR",
      tabAudio: "Call Recording",
      tabText: "Pasted Message",
      tabWhatsapp: "WhatsApp Bot",
      dropImagePrompt: "Click to upload or drag & drop suspicious screenshot or payment QR",
      dropImageHint: "Supports PNG, JPG, WEBP (Max 10MB)",
      dropAudioPrompt: "Upload suspicious call recording or audio note",
      dropAudioHint: "Supports MP3, WAV, M4A, OGG (Max 25MB)",
      pastePlaceholder: "Paste suspicious SMS, WhatsApp message, email, or UPI request note here...",
      scanButton: "SCAN & ANALYZE WITH CYBERGUARD AI",
      scanningButton: "ANALYZING MULTIMODAL TELEMETRY...",
      changeFile: "Click to change file",
      waTitle: "WhatsApp Bot Scam Interceptor Simulator",
      waSubtitle: "Simulate incoming WhatsApp scam messages and auto-trigger safety actions.",
      waPresetsLabel: "Quick Test Presets:",
      waPresetKyc: "SBI KYC Scam",
      waPresetElectricity: "Electricity Disconnect",
      waPresetArrest: "Digital Arrest Threat",
      waPlaceholder: "Type or select a suspicious WhatsApp message...",
      waSendBtn: "Simulate Message",
      waAnalyzingBtn: "Analyzing...",
      waBlockedBadge: "Threat Neutralized - Sender Blocked",
      waBlockBtn: "1-Tap Block Fraudster",
      waBlockingBtn: "Blocking...",
      waSafeBadge: "Message Safe - No Extortion Detected",
      waDangerBadge: "High Danger Scam Detected",
    },
    threat: {
      riskScoreLabel: "Risk Score",
      downloadReport: "Download Cybercrime PDF Report",
      generatingPdf: "Generating Official Report...",
      listenAdvisory: "Listen Audio Advisory",
      playingAudio: "Playing Advisory...",
      advisoryHeading: "AI Safety Advisory",
    },
    actions: {
      actionsHeading: "Immediate Protective Actions",
      emergencyHeading: "Emergency Cyber Helpline",
      emergencySub: "If you transferred money or shared your OTP:",
      dialHelpline: "Dial 1930",
      nationalPortal: "cybercrime.gov.in",
    },
    evidence: {
      evidenceHeading: "Forensic Evidence & Findings",
      noEvidence: "No forensic anomalies identified.",
      detectedBrand: "Impersonated Identity",
      urlAnalysis: "URL / Domain Analysis",
      upiAnalysis: "UPI Payment Analysis",
      audioAnalysis: "Acoustic Threat Analysis",
      flags: "Detected Threat Flags",
    },
    footer: {
      desc: "Dedicated to protecting citizens against digital extortion, fake parcel scams, and UPI collect fraud.",
      legal: "Official Indian Cyber Crime Reporting: Dial 1930 or visit cybercrime.gov.in",
    },
  },
  hi: {
    header: {
      subtitle: "मल्टीमॉडल फ्रॉड एवं स्कैम सुरक्षा",
      helpline: "1930 हेल्पलाइन",
    },
    hero: {
      badge: "वित्तीय जबरन वसूली से नागरिकों की सुरक्षा",
      title1: "कभी भी ",
      titleHighlight: "डिजिटल अरेस्ट या UPI फ्रॉड",
      title2: " के शिकार न बनें।",
      desc: "संदिग्ध स्क्रीनशॉट, पेमेंट QR कोड या धमकी भरे कॉल की रिकॉर्डिंग अपलोड करें। हमारा मल्टी-एजेंट AI तुरंत जांच करता है और आधिकारिक साइबर अपराध रिपोर्ट तैयार करता है।",
      badgeOcr: "स्क्रीनशॉट OCR",
      badgeQr: "UPI कलेक्ट QR डिकोडर",
      badgeAudio: "कॉल धमकी ध्वनि विश्लेषण",
    },
    upload: {
      tabImage: "स्क्रीनशॉट / QR",
      tabAudio: "कॉल रिकॉर्डिंग",
      tabText: "मैसेज पेस्ट करें",
      tabWhatsapp: "व्हाट्सएप बॉट",
      dropImagePrompt: "संदिग्ध स्क्रीनशॉट या QR कोड अपलोड करने के लिए क्लिक करें या ड्रैग करें",
      dropImageHint: "PNG, JPG, WEBP समर्थित (अधिकतम 10MB)",
      dropAudioPrompt: "संदिग्ध कॉल रिकॉर्डिंग या ऑडियो नोट अपलोड करें",
      dropAudioHint: "MP3, WAV, M4A, OGG समर्थित (अधिकतम 25MB)",
      pastePlaceholder: "संदिग्ध SMS, व्हाट्सएप मैसेज, ईमेल या UPI नोट यहाँ पेस्ट करें...",
      scanButton: "साइबरगार्ड AI से तुरंत जांच करें",
      scanningButton: "डेटा और साइबर रिकॉर्ड्स की जांच हो रही है...",
      changeFile: "फ़ाइल बदलने के लिए क्लिक करें",
      waTitle: "व्हाट्सएप बॉट फ्रॉड सिम्युलेटर",
      waSubtitle: "आने वाले व्हाट्सएप फ्रॉड संदेशों का परीक्षण करें और सुरक्षा अलर्ट प्राप्त करें।",
      waPresetsLabel: "त्वरित परीक्षण उदाहरण:",
      waPresetKyc: "SBI KYC स्कैम",
      waPresetElectricity: "बिजली बिल डिस्कनेक्ट",
      waPresetArrest: "डिजिटल अरेस्ट धमकी",
      waPlaceholder: "संदिग्ध व्हाट्सएप संदेश लिखें या चुनें...",
      waSendBtn: "मैसेज भेजें",
      waAnalyzingBtn: "जांच जारी है...",
      waBlockedBadge: "धमकी समाप्त - फ्रॉड नंबर ब्लॉक कर दिया गया",
      waBlockBtn: "1-क्लिक में फ्रॉडस्टर को ब्लॉक करें",
      waBlockingBtn: "ब्लॉक किया जा रहा है...",
      waSafeBadge: "संदेश सुरक्षित है - कोई जबरन वसूली नहीं",
      waDangerBadge: "गंभीर साइबर खतरा पाया गया",
    },
    threat: {
      riskScoreLabel: "जोखिम स्कोर",
      downloadReport: "साइबर अपराध PDF रिपोर्ट डाउनलोड करें",
      generatingPdf: "रिपोर्ट तैयार हो रही है...",
      listenAdvisory: "ऑडियो चेतावनी सुनें",
      playingAudio: "ऑडियो चल रहा है...",
      advisoryHeading: "AI सुरक्षा सलाह",
    },
    actions: {
      actionsHeading: "तुरंत सुरक्षात्मक कदम उठाएं",
      emergencyHeading: "आपातकालीन साइबर हेल्पलाइन",
      emergencySub: "यदि आपने पैसे ट्रांसफर कर दिए हैं या OTP शेयर कर दिया है:",
      dialHelpline: "1930 डायल करें",
      nationalPortal: "cybercrime.gov.in",
    },
    evidence: {
      evidenceHeading: "फॉरेंसिक साक्ष्य एवं निष्कर्ष",
      noEvidence: "कोई असामान्य खतरा नहीं मिला।",
      detectedBrand: "नकली पहचान / ब्रांड",
      urlAnalysis: "वेबसाइट / डोमेन विश्लेषण",
      upiAnalysis: "UPI भुगतान विश्लेषण",
      audioAnalysis: "आवाज़ एवं धमकी विश्लेषण",
      flags: "पहचाने गए खतरे",
    },
    footer: {
      desc: "डिजिटल अरेस्ट, फर्जी कूरियर पार्सल और UPI फ्रॉड से नागरिकों की सुरक्षा के लिए समर्पित।",
      legal: "भारत सरकार राष्ट्रीय साइबर अपराध रिपोर्टिंग: 1930 डायल करें या cybercrime.gov.in पर जाएं",
    },
  },
  te: {
    header: {
      subtitle: "మల్టీమోడల్ సైబర్ మోసాల రక్షణ వ్యవస్థ",
      helpline: "1930 హెల్ప్‌లైన్",
    },
    hero: {
      badge: "ఆర్థిక బెదిరింపుల నుండి పౌరుల రక్షణ",
      title1: "ఇకపై ఎప్పటికీ ",
      titleHighlight: "డిజిటల్ అరెస్ట్ లేదా UPI మోసాలలో",
      title2: " చిక్కుకోవద్దు.",
      desc: "అనుమానాస్పద స్క్రీన్‌షాట్, చెల్లింపు QR కోడ్ లేదా బెదిరింపు కాల్ రికార్డింగ్‌ను అప్‌లోడ్ చేయండి. మా AI వ్యవస్థ రియల్ టైమ్‌లో పరిశీలించి అధికారిక సైబర్‌క్రైమ్ నివేదికను అందిస్తుంది.",
      badgeOcr: "స్క్రీన్‌షాట్ OCR",
      badgeQr: "UPI కలెక్ట్ QR డీకోడర్",
      badgeAudio: "కాల్ బెదిరింపు వాయిస్ విశ్లేషణ",
    },
    upload: {
      tabImage: "స్క్రీన్‌షాట్ / QR",
      tabAudio: "కాల్ రికార్డింగ్",
      tabText: "సందేశం అతికించండి",
      tabWhatsapp: "వాట్సాప్ బాట్",
      dropImagePrompt: "స్క్రీన్‌షాట్ లేదా QR కోడ్‌ను అప్‌లోడ్ చేయడానికి క్లిక్ చేయండి లేదా డ్రాగ్ చేయండి",
      dropImageHint: "PNG, JPG, WEBP సపోర్ట్ (గరిష్టంగా 10MB)",
      dropAudioPrompt: "బెదిరింపు కాల్ రికార్డింగ్ లేదా ఆడియోను అప్‌లోడ్ చేయండి",
      dropAudioHint: "MP3, WAV, M4A, OGG సపోర్ట్ (గరిష్టంగా 25MB)",
      pastePlaceholder: "అనుమానాస్పద SMS, వాట్సాప్ సందేశం లేదా UPI నోట్‌ను ఇక్కడ పేస్ట్ చేయండి...",
      scanButton: "సైబర్‌గార్డ్ AI తో స్కాన్ & విశ్లేషించండి",
      scanningButton: "డేటాను విశ్లేషిస్తోంది...",
      changeFile: "ఫైల్ మార్చడానికి క్లిక్ చేయండి",
      waTitle: "వాట్సాప్ బాట్ మోసాల నిరోధక సిమ్యులేటర్",
      waSubtitle: "వాట్సాప్ మోసపూరిత సందేశాలను పరీక్షించి భద్రతా చర్యలను పొందండి.",
      waPresetsLabel: "త్వరిత నమూనాలు:",
      waPresetKyc: "SBI KYC మోసం",
      waPresetElectricity: "కరెంట్ బిల్లు డిస్‌కనెక్ట్",
      waPresetArrest: "డిజిటల్ అరెస్ట్ బెదిరింపు",
      waPlaceholder: "వాట్సాప్ సందేశాన్ని నమోదు చేయండి...",
      waSendBtn: "సందేశం పంపండి",
      waAnalyzingBtn: "పరిశీలిస్తోంది...",
      waBlockedBadge: "ముప్పు నివారించబడింది - నంబర్ బ్లాక్ చేయబడింది",
      waBlockBtn: "1-క్లిక్‌తో మోసగాడిని బ్లాక్ చేయండి",
      waBlockingBtn: "బ్లాక్ చేస్తోంది...",
      waSafeBadge: "సందేశం సురక్షితం - ఎటువంటి ముప్పు లేదు",
      waDangerBadge: "తీవ్రమైన సైబర్ మోసం గుర్తించబడింది",
    },
    threat: {
      riskScoreLabel: "ప్రమాద స్కోర్",
      downloadReport: "సైబర్‌క్రైమ్ PDF నివేదికను డౌన్‌లోడ్ చేయండి",
      generatingPdf: "నివేదిక తయారవుతోంది...",
      listenAdvisory: "ఆడియో హెచ్చరిక వినండి",
      playingAudio: "ఆడియో ప్లే అవుతోంది...",
      advisoryHeading: "AI భద్రతా సలహా",
    },
    actions: {
      actionsHeading: "వెంటనే తీసుకోవలసిన రక్షణ చర్యలు",
      emergencyHeading: "అత్యవసర సైబర్ హెల్ప్‌లైన్",
      emergencySub: "మీరు డబ్బు పంపినా లేదా OTP షేర్ చేసినా:",
      dialHelpline: "1930 కి కాల్ చేయండి",
      nationalPortal: "cybercrime.gov.in",
    },
    evidence: {
      evidenceHeading: "ఫోరెన్సిక్ సాక్ష్యాలు & వివరాలు",
      noEvidence: "ఎటువంటి అనుమానాస్పద అంశాలు లేవు.",
      detectedBrand: "నకిలీ గుర్తింపు",
      urlAnalysis: "వెబ్‌సైట్ / లింక్ విశ్లేషణ",
      upiAnalysis: "UPI చెల్లింపు విశ్లేషణ",
      audioAnalysis: "వాయిస్ & బెదిరింపు విశ్లేషణ",
      flags: "గుర్తించిన ప్రమాద హెచ్చరికలు",
    },
    footer: {
      desc: "డిజిటల్ అరెస్ట్, నకిలీ కొరియర్ పార్సెల్ మరియు UPI మోసాల నుండి పౌరులను రక్షించడానికి రూపొందించబడింది.",
      legal: "భారత ప్రభుత్వం జాతీయ సైబర్ క్రైమ్ హెల్ప్‌లైన్: 1930 డయల్ చేయండి లేదా cybercrime.gov.in సందర్శించండి",
    },
  },
  ta: {
    header: {
      subtitle: "மல்டிமாடல் மோசடி தடுப்பு பாதுகாப்பு",
      helpline: "1930 உதவி எண்",
    },
    hero: {
      badge: "நிதி மிரட்டல்களில் இருந்து குடிமக்கள் பாதுகாப்பு",
      title1: "இனி ஒருபோதும் ",
      titleHighlight: "டிஜிட்டல் கைது அல்லது UPI மோசடியில்",
      title2: " சிக்காதீர்கள்.",
      desc: "சந்தேகத்திற்குரிய ஸ்கிரீன்ஷாட், QR குறியீடு அல்லது மிரட்டல் அழைப்புப் பதிவை பதிவேற்றவும். எங்கள் AI உடனடியாக சரிபார்த்து அதிகாரப்பூர்வ சைபர்கிரைம் அறிக்கையை வழங்குகிறது.",
      badgeOcr: "ஸ்கிரீன்ஷாட் OCR",
      badgeQr: "UPI QR குறிவிலக்கி",
      badgeAudio: "அழைப்பு அச்சுறுத்தல் ஒலி பகுப்பாய்வு",
    },
    upload: {
      tabImage: "ஸ்கிரீன்ஷாட் / QR",
      tabAudio: "அழைப்பு பதிவு",
      tabText: "செய்தியை ஒட்டுக",
      tabWhatsapp: "வாட்ஸ்அப் பாட்",
      dropImagePrompt: "ஸ்கிரீன்ஷாட் அல்லது QR குறியீட்டை பதிவேற்ற கிளிக் செய்யவும் அல்லது இழுக்கவும்",
      dropImageHint: "PNG, JPG, WEBP ஆதரிக்கப்படுகிறது (அதிகபட்சம் 10MB)",
      dropAudioPrompt: "சந்தேகத்திற்குரிய அழைப்பு ஆடியோவை பதிவேற்றவும்",
      dropAudioHint: "MP3, WAV, M4A, OGG ஆதரிக்கப்படுகிறது (அதிகபட்சம் 25MB)",
      pastePlaceholder: "சந்தேகத்திற்குரிய SMS, வாட்ஸ்அப் செய்தி அல்லது UPI குறிப்பை இங்கே ஒட்டவும்...",
      scanButton: "சைபர்கார்ட் AI மூலம் ஸ்கேன் செய்து பகுப்பாய்வு செய்க",
      scanningButton: "பகுப்பாய்வு செய்யப்படுகிறது...",
      changeFile: "கோப்பை மாற்ற கிளிக் செய்யவும்",
      waTitle: "வாட்ஸ்அப் பாட் மோசடி தடுப்பு மாதிரி",
      waSubtitle: "வாட்ஸ்அப் மோசடி செய்திகளை உருவகப்படுத்தி பாதுகாப்பு நடவடிக்கைகளைத் தூண்டவும்.",
      waPresetsLabel: "விரைவு சோதனை மாதிரிகள்:",
      waPresetKyc: "SBI KYC மோசடி",
      waPresetElectricity: "மின் கட்டண துண்டிப்பு",
      waPresetArrest: "டிஜிட்டல் கைது மிரட்டல்",
      waPlaceholder: "வாட்ஸ்அப் செய்தியை உள்ளிடவும்...",
      waSendBtn: "செய்தி அனுப்புக",
      waAnalyzingBtn: "ஆராய்கிறது...",
      waBlockedBadge: "அச்சுறுத்தல் நீக்கப்பட்டது - எண் தடுக்கப்பட்டது",
      waBlockBtn: "1-கிளிக்கில் மோசடிக்காரரை தடு (Block)",
      waBlockingBtn: "தடுக்கப்படுகிறது...",
      waSafeBadge: "செய்தி பாதுகாப்பானது - அச்சுறுத்தல் இல்லை",
      waDangerBadge: "ஆபத்தான சைபர் மோசடி கண்டறியப்பட்டது",
    },
    threat: {
      riskScoreLabel: "ஆபத்து மதிப்பெண்",
      downloadReport: "சைபர்கிரைம் PDF அறிக்கையை பதிவிறக்குக",
      generatingPdf: "அறிக்கை தயாராகிறது...",
      listenAdvisory: "ஆடியோ ஆலோசனையைக் கேளுங்கள்",
      playingAudio: "ஆடியோ இயங்குகிறது...",
      advisoryHeading: "AI பாதுகாப்பு ஆலோசனை",
    },
    actions: {
      actionsHeading: "உடனடி பாதுகாப்பு நடவடிக்கைகள்",
      emergencyHeading: "அவசர சைபர் உதவி எண்",
      emergencySub: "நீங்கள் பணம் அனுப்பியிருந்தால் அல்லது OTP பகிர்ந்திருந்தால்:",
      dialHelpline: "1930 அழைக்கவும்",
      nationalPortal: "cybercrime.gov.in",
    },
    evidence: {
      evidenceHeading: "தடயவியல் சான்றுகள்",
      noEvidence: "சந்தேகத்திற்குரிய அச்சுறுத்தல்கள் இல்லை.",
      detectedBrand: "போலி அடையாளம்",
      urlAnalysis: "வலைத்தள பகுப்பாய்வு",
      upiAnalysis: "UPI கட்டண பகுப்பாய்வு",
      audioAnalysis: "குரல் மற்றும் ஒலி பகுப்பாய்வு",
      flags: "கண்டறியப்பட்ட எச்சரிக்கைகள்",
    },
    footer: {
      desc: "டிஜிட்டல் கைது, போலி பார்சல் மோசடிகள் மற்றும் UPI மோசடிகளில் இருந்து பொதுமக்களைப் பாதுகாக்க உருவாக்கப்பட்டது.",
      legal: "இந்திய தேசிய சைபர் கிரைம் உதவி: 1930 அல்லது cybercrime.gov.in பார்க்கவும்",
    },
  },
  bn: {
    header: {
      subtitle: "মাল্টিমোডাল প্রতারণা ও স্ক্যাম সুরক্ষা",
      helpline: "১৯৩০ হেল্পলাইন",
    },
    hero: {
      badge: "আর্থিক তোলাবাজি থেকে নাগরিকদের সুরক্ষা",
      title1: "আর কখনোই ",
      titleHighlight: "ডিজিটাল অ্যারেস্ট বা UPI প্রতারণার",
      title2: " শিকার হবেন না।",
      desc: "সন্দেহজনক স্ক্রিনশট, পেমেন্ট QR কোড বা হুমকি দেওয়া কল রেকর্ডিং আপলোড করুন। আমাদের AI তৎক্ষণাৎ তদন্ত করে অফিসিয়াল সাইবার ক্রাইম রিপোর্ট তৈরি করে।",
      badgeOcr: "স্ক্রিনশট OCR",
      badgeQr: "UPI QR ডিকোডার",
      badgeAudio: "কল হুমকি ভয়েস বিশ্লেষণ",
    },
    upload: {
      tabImage: "স্ক্রিনশট / QR",
      tabAudio: "কল রেকর্ডিং",
      tabText: "মেসেজ পেস্ট করুন",
      tabWhatsapp: "হোয়াটসঅ্যাপ বট",
      dropImagePrompt: "স্ক্রিনশট বা QR কোড আপলোড করতে ক্লিক করুন বা ড্র্যাগ করুন",
      dropImageHint: "PNG, JPG, WEBP সমর্থিত (সর্বোচ্চ 10MB)",
      dropAudioPrompt: "সন্দেহজনক কল রেকর্ডিং বা অডিও আপলোড করুন",
      dropAudioHint: "MP3, WAV, M4A, OGG সমর্থিত (সর্বোচ্চ 25MB)",
      pastePlaceholder: "সন্দেহজনক SMS, হোয়াটসঅ্যাপ বার্তা বা UPI নোট এখানে পেস্ট করুন...",
      scanButton: "সাইবারগার্ড AI দিয়ে স্ক্যান ও বিশ্লেষণ করুন",
      scanningButton: "তথ্য বিশ্লেষণ করা হচ্ছে...",
      changeFile: "ফাইল পরিবর্তন করতে ক্লিক করুন",
      waTitle: "হোয়াটসঅ্যাপ বট স্ক্যাম সিমুলেটর",
      waSubtitle: "হোয়াটসঅ্যাপের প্রতারণামূলক বার্তা পরীক্ষা করুন এবং তাৎক্ষণিক নিরাপত্তা সতর্কতা পান।",
      waPresetsLabel: "দ্রুত পরীক্ষার নমুনা:",
      waPresetKyc: "SBI KYC স্ক্যাম",
      waPresetElectricity: "বিদ্যুৎ বিল সংযোগ বিচ্ছিন্ন",
      waPresetArrest: "ডিজিটাল অ্যারেস্ট হুমকি",
      waPlaceholder: "হোয়াটসঅ্যাপ মেসেজ লিখুন বা নির্বাচন করুন...",
      waSendBtn: "বার্তা পাঠান",
      waAnalyzingBtn: "বিশ্লেষণ চলছে...",
      waBlockedBadge: "হুমকি নিষ্ক্রিয় - প্রেরককে ব্লক করা হয়েছে",
      waBlockBtn: "১-ক্লিকে প্রতারককে ব্লক করুন",
      waBlockingBtn: "ব্লক করা হচ্ছে...",
      waSafeBadge: "বার্তাটি নিরাপদ - কোনো তোলাবাজি নেই",
      waDangerBadge: "মারাত্মক সাইবার প্রতারণা চিহ্নিত",
    },
    threat: {
      riskScoreLabel: "ঝুঁকি স্কোর",
      downloadReport: "সাইবার ক্রাইম PDF রিপোর্ট ডাউনলোড করুন",
      generatingPdf: "রিপোর্ট তৈরি হচ্ছে...",
      listenAdvisory: "অডিও সতর্কতা শুনুন",
      playingAudio: "অডিও চলছে...",
      advisoryHeading: "AI নিরাপত্তা নির্দেশিকা",
    },
    actions: {
      actionsHeading: "তাৎক্ষণিক সুরক্ষামূলক পদক্ষেপ",
      emergencyHeading: "জরুরি সাইবার হেল্পলাইন",
      emergencySub: "আপনি টাকা পাঠিয়ে থাকলে বা OTP শেয়ার করে থাকলে:",
      dialHelpline: "১৯৩০ ডায়াল করুন",
      nationalPortal: "cybercrime.gov.in",
    },
    evidence: {
      evidenceHeading: "ফরেনসিক প্রমাণ ও পর্যবেক্ষণ",
      noEvidence: "কোনো সন্দেহজনক উপাদান পাওয়া যায়নি।",
      detectedBrand: "ভুয়ো পরিচয়",
      urlAnalysis: "ওয়েবসাইট / ডোমেন বিশ্লেষণ",
      upiAnalysis: "UPI পেমেন্ট বিশ্লেষণ",
      audioAnalysis: "কণ্ঠস্বর ও হুমকি বিশ্লেষণ",
      flags: "চিহ্নিত ঝুঁকির কারণ",
    },
    footer: {
      desc: "ডিজিটাল গ্রেফতারি, ভুয়ো পার্সেল এবং UPI প্রতারণা থেকে নাগরিকদের রক্ষার জন্য তৈরি।",
      legal: "ভারত সরকারের জাতীয় সাইবার ক্রাইম হেল্পলাইন: ১৯৩০ বা cybercrime.gov.in দেখুন",
    },
  },
};

export function getTranslation(lang: string): TranslationDict {
  const code = (lang as SupportedLanguage) in translations ? (lang as SupportedLanguage) : "en";
  return translations[code];
}

