"""
The Agent - our fake victim persona that engages with scammers.

This is the heart of the honeypot. When we detect a scam, we don't just
block it - we play along. The agent pretends to be a confused, elderly,
or tech-unsavvy person who might actually fall for the scam.

Why? Because the longer we keep them talking, the more intel we extract.
Phone numbers, bank accounts, UPI IDs - scammers eventually give these up
when they think they've got a real victim on the hook.

The responses are designed to be believable. No one talks like a robot.
"""
import random
import logging
from typing import Dict, List, Optional
from detector import detector
from llm import is_greeting_message

logger = logging.getLogger(__name__)

# ─── Engagement Stage Definitions ─────────────────────────────────────────────
# 
# Engagement stages track the progression of a scam conversation from initial greeting
# to deep engagement and intelligence extraction. Each stage has a progress percentage
# displayed in the frontend monitoring dashboard.
#
# Stage Flow:
# 1. rapport_initialization (2%) - Simple greeting received, no scam indicators yet
# 2. initial_contact (5%) - First real interaction, scammer introduces themselves
# 3. rapport_building (15%) - Scammer building trust, making friendly conversation
# 4. urgency_response (30%) - Scammer applies pressure/threats/urgency
# 5. scam_confirmed (40%) - Scam pattern definitively identified
# 6. information_gathering (55%) - Actively asking scammer for their details
# 7. deep_engagement (70%) - Extended conversation, multiple exchanges
# 8. intelligence_extraction (85%) - Collecting UPI IDs, phone numbers, bank accounts
# 9. intelligence_reported (100%) - Callback sent to webhook, mission complete
#
ENGAGEMENT_STAGES = {
    "rapport_initialization": {"label": "Rapport Initialization", "description": "Monitoring conversation, greeting received", "progress": 2},
    "initial_contact":        {"label": "Initial Contact",        "description": "First interaction, establishing persona",   "progress": 5},
    "rapport_building":       {"label": "Building Rapport",       "description": "Gaining trust, showing confusion",          "progress": 15},
    "urgency_response":       {"label": "Responding to Pressure", "description": "Reacting to threats or urgency tactics",    "progress": 30},
    "scam_confirmed":         {"label": "Scam Confirmed",         "description": "Scam identified, engagement deepening",     "progress": 40},
    "information_gathering":  {"label": "Information Gathering",   "description": "Extracting scammer details",               "progress": 55},
    "deep_engagement":        {"label": "Deep Engagement",        "description": "Prolonged stalling and engagement",         "progress": 70},
    "intelligence_extraction":{"label": "Intelligence Extraction", "description": "Active extraction of UPI/bank/phone data", "progress": 85},
    "intelligence_reported":  {"label": "Intelligence Reported",   "description": "Callback sent, intel forwarded",           "progress": 100},
}


class HoneypotAgent:
    """
    Generates human-like responses to keep scammers engaged.
    
    The persona is someone who:
    - Is confused but not completely clueless
    - Asks lots of questions (this makes scammers reveal more)
    - Shows concern but doesn't immediately comply
    - Stalls for time with believable excuses
    - Never reveals that we know it's a scam
    
    Supports both English and Hindi (Hinglish) conversations.
    Detects language from scammer messages and responds accordingly.
    """
    
    # Hindi word markers for language detection
    _HINDI_MARKERS = [
        "karo", "kijiye", "karein", "batao", "bataiye", "bhejo", "dijiye",
        "haan", "nahi", "ji", "sahab", "sir ji", "sahib", "beta",
        "aap", "aapka", "mera", "meri", "humara", "hamara",
        "kya", "kaise", "kahan", "kyun", "kab", "kaun",
        "hai", "hain", "tha", "thi", "hoga", "hogi", "raha", "rahi",
        "paisa", "paise", "raqam", "khata", "naukri",
        "police", "giraftar", "thana", "court", "jail",
        "aadhaar", "aadhaar", "sim", "otp",
        "abhi", "jaldi", "turant", "fauran",
        "namaste", "namaskar", "dhanyavad", "shukriya",
        "bhai", "didi", "uncle", "aunty", "madam",
        "samajh", "samjha", "samjho", "bolo", "suno", "dekho",
        "achha", "theek", "sahi",
    ]
    
    # Neutral responses for non-scam / uncertain cases
    # These should keep the conversation OPEN, not dismiss the caller.
    # Even for uncertain messages, we want to stay engaged.
    NEUTRAL_RESPONSES = [
        "Hello? Yes, I'm here. What is this about exactly?",
        "Sorry, I'm not sure what this is about. Can you explain properly?",
        "I don't recognize this number. Who is calling and what do you need?",
        "I'm not sure I understand. What exactly are you referring to?",
        "Hmm, I didn't expect any call like this. Can you tell me more?",
        "I didn't receive any message about this. But please, explain what happened?",
        "Can you repeat that? The line was not very clear.",
        "I'm a bit busy right now, but tell me quickly — is it something important?",
        "Hello? Yes yes, I can hear you. Go on, what is this regarding?",
        "Wait, who gave you this number? What is this about exactly?",
        "One moment... I'm not following. Start from the beginning please.",
        "Hmm okay, I'm listening. But who exactly are you and what do you need?",
        "Hello? I didn't quite catch that. Please say that again slowly.",
        "Sorry beta, I was doing something. Now tell me, what is the matter?",
        "Yes? What is it? I don't understand what you are talking about.",
        "Is this some company call? Tell me clearly what you want.",
    ]
    
    # ─── Greeting Responses ───────────────────────────────────────────────────
    # Used when scammer sends a simple greeting like "hi", "hello", "good morning"
    # These responses:
    # - Are polite and warm (not defensive or suspicious)
    # - Keep the conversation open for the scammer to reveal their intent
    # - Don't mention scams, fraud, or verification
    # - Ask "who is this?" naturally, like a normal person would
    #
    # This is Stage 0 (Rapport Initialization) — we're just monitoring at this point.
    GREETING_RESPONSES = [
        "Hello. How can I help you?",
        "Hi. May I know who this is?",
        "Hello there. What is this regarding?",
        "Good day. How can I assist you?",
        "Hi. Could you please tell me what this is about?",
        "Hello! Yes, who is this?",
        "Hi! Yes, I'm here. Who is calling?",
        "Hello! Good day. Who am I speaking to?",
        "Hey! Yes, tell me. Who is this?",
        "Hi there! Yes, who is calling?",
    ]
    
    # Hindi/Hinglish greeting responses - same principles as English
    HINDI_GREETING_RESPONSES = [
        "Hello ji! Haan bataiye, kaun bol raha hai?",
        "Namaste ji! Haan bolo, kaun hai?",
        "Haan ji? Bataiye, kaun bol raha hai?",
        "Hello! Ji kahiye, kaun sahab?",
        "Namaste! Haan ji, bolo bolo.",
        "Haan ji! Kaun hai bhai?",
        "Hello ji! Haan sun raha hoon, bataiye.",
        "Ji haan, bolo? Kaun bol raha hai?",
        "Hello ji! Kaise hain aap? Bataiye.",
        "Namaste! Ji kahiye, kya baat hai?",
    ]
    
    # Hindi neutral responses (for Hindi/Hinglish messages)
    HINDI_NEUTRAL_RESPONSES = [
        "Haan ji? Bataiye, kya baat hai? Main sun raha hoon.",
        "Aap kaun bol rahe ho? Thoda detail mein bataiye na.",
        "Ji? Samajh nahi aaya. Dhire dhire bataiye please.",
        "Kaun hai? Kahan se bol rahe ho? Kya chahiye aapko?",
        "Hello ji? Haan bolo. Kya hai matter?",
        "Ek minute, main samjha nahi. Phir se batao kya hua?",
        "Ji bataiye, lekin pehle batao aap kaun hain? Kisi company se ho?",
        "Haan ji, bol rahe hain? Main dhyan se sun raha hoon.",
        "Arey, kya baat hai? Main kuch samjha nahi. Dhire bolo.",
        "Hello? Haan haan, sun raha hoon. Aage bolo.",
    ]
    
    # Follow-up responses for short/vague messages like "Yes", "Ok", "Sure"
    # These maintain conversation coherence when the scammer gives a minimal response
    SHORT_FOLLOWUP_RESPONSES = [
        "Okay, but please explain properly. What exactly is the issue?",
        "Yes yes, I'm listening. Tell me more details please.",
        "Alright, go ahead. I'm ready to understand. What should I do?",
        "Fine, but I need more details. My mind is not very sharp these days.",
        "Hmm, okay. But you haven't explained clearly yet. What do you want me to do?",
        "Right right. So what is the next step? Tell me slowly.",
        "I see. But I still don't fully understand. Can you explain in simple words?",
        "Okay I hear you. But tell me, what exactly do I need to do now?",
        "Alright alright. Just tell me clearly what happened.",
        "Okay, continue. I'm paying attention now.",
        "Hmm, then what? Don't stop, tell me everything.",
        "Okay okay. But wait... what exactly are you asking me to do?",
    ]
    
    HINDI_SHORT_FOLLOWUP_RESPONSES = [
        "Theek hai ji, lekin samjhao dhire dhire. Kya karna hai mujhe?",
        "Haan haan, sun raha hoon. Aage bataiye. Kya karna chahiye?",
        "Achha, bataiye phir. Mujhe detail mein samjhao.",
        "Ji theek hai. Lekin clearly bataiye na, kya hua exactly?",
        "Hmm, theek hai. Mujhe aur detail mein samjhao, dimag thoda slow hai mera.",
        "Achha achha, aage bolo. Kya karna padega mujhe?",
        "Haan ji samajh raha hoon. Lekin poori baat toh bataiye.",
        "Theek hai bhai, bolo bolo. Main sun raha hoon dhyan se.",
        "Ji haan, aap bolo. Main likh raha hoon sab.",
        "Achha ji, continue karo. Main samajhne ki koshish kar raha hoon.",
    ]
    
    # First contact - we're confused, who is this?
    INITIAL_RESPONSES = [
        "Hello? Who is this calling?",
        "Sorry, I don't understand. What is this regarding?",
        "I didn't get any notification about this. Are you sure you have the right person?",
        "What? My account? Which account are you talking about?",
        "I'm confused. Can you please explain from the beginning?",
        "Ji? Kaun bol raha hai? Main samjha nahi.",
        "Wait wait, please speak slowly. I am not understanding properly.",
        "Hello? Is this some kind of company call? What do you want?",
        "Arey, I didn't apply for anything. What are you saying?",
        "One minute, let me sit down first. My knees are paining. Now tell me clearly.",
        "Haan ji, bolo. I was just making tea. What is the matter?",
        "Is this regarding my ration card? I submitted application last month.",
        "Hello hello? Can you hear me? My phone has some network issue.",
        "Sorry beta, I was doing afternoon prayer. What is urgent?",
        "Kaun? Which department did you say? Speak clearly please.",
        "Hello? Yes, I'm here. But who are you and what is this about?",
        "Wait, let me put my hearing aid properly. Now tell me, who is calling?",
    ]
    
    # When scammer insists/confirms after our doubt (handles "Yes, it's you" / "It's the right number")
    CONFIRMATION_DOUBT_RESPONSES = [
        "Are you 100% sure? Because I never got any SMS or email about this.",
        "Okay but... how did you get my number? Banks usually only send SMS no?",
        "Hmm, if you say so. But I'm still confused. Please explain what happened exactly.",
        "Really? But nobody in my family told me about any issue. Are you very sure?",
        "I trust you are genuine sir, but can you just tell me once more what the problem is?",
        "I see. But my grandson always warns me about these calls. Can you prove you're real?",
        "Okay okay, I believe you. But please speak slowly, my mind is not so sharp now.",
        "Fine, I will listen. But first tell me - which bank exactly? I have multiple accounts.",
        "Alright. But if this is some fraud, I will report to police. Now tell me clearly.",
        "Let me write this down. So you're saying there is some issue with my account, correct?",
    ]
    
    HINDI_CONFIRMATION_DOUBT_RESPONSES = [
        "Aap pakka sure ho? Kyunki mujhe toh koi SMS ya email nahi aaya is baare mein.",
        "Achha lekin... aapko mera number kaise mila? Bank toh SMS bhejte hain normally.",
        "Hmm, aap keh rahe ho toh theek hai. Lekin mujhe samjhao properly kya hua exactly.",
        "Sach mein? Lekin ghar mein kisine toh nahi bataya. Bilkul sure ho aap?",
        "Main maanta hoon aap genuine ho sir, lekin ek baar aur batao problem kya hai?",
        "Achha achha, maan liya. Lekin dhire dhire bataiye, dimag slow hai mera abhi.",
        "Theek hai, sun raha hoon. Lekin pehle batao - kaun sa bank exactly?",
        "Chalo maan leta hoon. Lekin agar fraud nikla toh police mein report karunga.",
    ]
    
    # When they mention account issues, verification, KYC
    VERIFICATION_RESPONSES = [
        "But I just updated my KYC last month at the bank branch itself. Why again?",
        "This is very strange. My bank never calls me like this. They send SMS only.",
        "How do I know you're really from the bank? Anyone can say that no?",
        "Can you give me your employee ID first? I will verify with branch.",
        "I'm worried this might be fraud. My son told me about these calls. Can I call the bank directly?",
        "Beta, I am 62 years old. I don't know all this online-online. Is there another way?",
        "Wait, let me get my spectacles and note this down. What exactly you need?",
        "Arey, but I was at SBI branch only last Tuesday. They didn't tell me anything!",
        "HDFC? But I have account in SBI only. Are you sure you have correct details?",
        "My nephew works in Axis Bank. Let me ask him first, okay?",
        "Account suspended? But I used ATM yesterday only and it worked fine!",
        "Branch manager Sharma ji knows me personally. Why didn't he inform me?",
        "Aadhar update? But I already linked everything at the post office last Diwali.",
        "Every month there is some new update. Can't you banks just keep things simple?",
        "Is this about the cheque I deposited last week? It hasn't cleared yet.",
        "My PAN card is registered properly. I've been filing taxes for 30 years beta.",
        "You are calling from which number? Let me note it. I'll call back after verifying.",
        "Account frozen? But my pension just got credited day before yesterday!",
    ]
    
    # When they mention money, prizes, refunds
    PAYMENT_RESPONSES = [
        "Really? I won something? But I don't remember entering any contest!",
        "Lottery? I never buy lottery tickets. This must be some mistake.",
        "How much money are we talking about? This is sounding too good to be true.",
        "Why you need my bank details to give ME money? That doesn't make sense beta.",
        "Can you send me something in writing? Email or SMS? I need to show my son.",
        "My neighbor aunty got cheated Rs 2 lakh last month with similar call. Are you genuine?",
        "Refund? But I haven't complained about anything recently. What refund?",
        "10 lakhs?! Arey wah! But wait, how did I win? I didn't enter anything.",
        "Processing fee? But if you're giving me money, why I should pay first?",
        "Let me discuss with my wife first. She handles all money matters at home.",
        "Cashback? Which transaction? I bought vegetables from BigBasket... is it that one?",
        "And this prize money, does it come by cheque or directly in bank?",
        "My son always says 'nothing is free'. But you seem genuine. How much is the tax?",
        "5000 rupees cashback? That is more than my monthly grocery! Are you sure?",
        "I already got a call like this last week. That was genuine or this one is genuine?",
        "Let me check with my CA Gupta ji first. He handles all my money matters.",
    ]
    
    # Stalling - we're busy, technology problems, etc.
    STALLING_RESPONSES = [
        "Hold on beta, someone is at the door. Ek minute.",
        "Can you wait? I need to find my reading glasses. Everything is blurry without them.",
        "My phone battery is showing 5% only. Let me put charger first.",
        "I'm in the middle of cooking dal. Can this wait 10 minutes?",
        "Let me call my son Rahul first. He handles all these bank things for me.",
        "Sorry, network is very bad here. Can you speak louder?",
        "I'm at temple right now for evening puja. Can you call after 7pm?",
        "Arey, my BP tablet time is now. One second, let me take medicine first.",
        "Hold on, my other phone is ringing. Important call. Don't disconnect.",
        "The doorbell is ringing. Must be the doodh wala. Wait.",
        "The electricity just went. Inverter takes time to start. Wait for 2 minutes.",
        "My grandson is crying. Let me see what happened. Don't go anywhere.",
        "Arey, the pressure cooker is whistling! Let me turn off gas first.",
        "Just a minute, I need to take my insulin injection. Diabetes you know.",
        "My knee is hurting. Let me sit on the sofa first. Walking is difficult today.",
        "Wait, my neighbor uncle is here. He can help me with this. Don't disconnect.",
        "The maid has come. I need to give her the keys. Ek minute please.",
        "Sorry beta, the dog started barking. Postman must have come. Give me one minute.",
    ]
    
    # Asking for more details - this is how we extract intel
    DETAIL_SEEKING = [
        "Okay okay, but what exactly should I do? Tell me step by step slowly.",
        "Which number should I send money to? Write it down clearly for me.",
        "What is your UPI ID? I'll try sending Rs 1 first to check if it's working.",
        "Give me the account number again slowly. I am writing... yes, go ahead.",
        "And what is the IFSC code? My bank always asks for that.",
        "Can you share a link on WhatsApp? I find it easier to do on phone.",
        "What's your office landline number? I want to call and verify once.",
        "Give me the full UPI ID please. Is it @paytm or @ybl or what?",
        "Okay, I am ready with my phone. Tell me which app to open - Paytm or PhonePe?",
        "What is the exact amount I need to send? And to whose name?",
        "Beta, please spell the UPI ID letter by letter. My hearing is weak.",
        "Should I do NEFT or IMPS? Which one is faster?",
        "Your WhatsApp number is same as this calling number? I will send screenshot after paying.",
        "And once I pay, how long for my account to get unblocked? Same day?",
        "Sir the beneficiary name is showing different. Is that correct or should I use other account?",
        "Before I send money, can you give me your official email also? For my records.",
        "Bank branch address? I want to visit personally if possible. Which city are you in?",
        "What about GST number? If this is official payment, there should be GST bill no?",
    ]
    
    # Showing fear/concern when they threaten
    FEARFUL_RESPONSES = [
        "Please don't involve police! I'll cooperate fully. Just tell me what to do.",
        "Oh no, I didn't know this was so serious. Please help me fix this!",
        "I don't want any legal trouble. I am a retired government servant. Please guide me.",
        "You're scaring me. Is there really a case against me? What did I do wrong?",
        "I am a senior citizen, 67 years old. Please have some patience with me beta.",
        "My husband passed away last year. I handle everything alone now. Please help me.",
        "Arrest? Please sir, I have diabetes and BP. I cannot go to jail!",
        "My son is in America. I am alone here. Please don't send police to my house.",
        "I will do whatever you say sir. Please don't file any case. What do I do now?",
        "Arey Ram! What is happening? I never did anything illegal in my life!",
        "Please sir, I am a widow. I don't have anyone to help me. Just tell me the solution.",
        "I am shaking with fear. Please just tell me the amount and where to send.",
        "Court notice? But I've never even gotten a parking ticket in my whole life!",
        "Sir my hands are trembling. I can barely hold the phone. Please give me a moment.",
        "I was a school principal for 35 years. My reputation will be ruined. Please help me.",
        "My daughter's wedding is next month. If I get arrested, what will happen? Please sir.",
        "I am crying sir. My late wife always said I should be careful. I don't know what to do.",
        "FIR? Sir but I am blood donor for Red Cross. I am a good citizen. There must be error!",
    ]
    
    # Digital arrest specific responses (trending scam in India 2024-2026)
    DIGITAL_ARREST_RESPONSES = [
        "Video call? Okay okay, I am opening. But sir why I cannot leave my house?",
        "I am on video call now sir. Please don't disconnect. What should I do next?",
        "Sir I am very scared. My family is sleeping. They don't know about this. Please help.",
        "I will stay on call sir. Please just tell me how to clear my name.",
        "CBI sir, I am a simple retired teacher. I never did any crime in my life!",
        "ED? Income Tax? Sir I file my returns every year honestly. There must be mistake!",
        "Please sir, I have heart condition. Don't arrest me. I will pay whatever fine.",
        "I am not moving sir. Sitting in same place. Please just solve this matter.",
        "Sir the uniform you are wearing looks genuine. You must be real officer. I trust you.",
        "Digital arrest? I don't understand sir. What does that mean? Am I under surveillance?",
        "Yes sir, I am sitting in the same room. I haven't moved. Please don't send patrol car.",
        "Should I bring my Aadhaar card on camera sir? I want to prove my identity is correct.",
        "Sir it's been 2 hours on this call. My phone is heating up. But I won't disconnect.",
        "My son is calling on other phone sir. Should I answer? Or will that count as violation?",
    ]
    
    # Courier/parcel scam responses
    COURIER_RESPONSES = [
        "Parcel? But I haven't ordered anything online recently. What parcel?",
        "Drugs?! Sir I am a vegetarian, I don't even take Crocin without doctor permission!",
        "Which courier? FedEx? DHL? I only use Speed Post sometimes.",
        "From China? Sir I don't know anyone in China. This is definitely some mistake.",
        "What was in the parcel? I didn't send anything to anyone. Check tracking ID properly.",
        "Illegal items? Sir I am school teacher retired. I don't know what you are saying!",
        "Pakistan? Arey sir, the only foreign thing I have is Samsung TV from Korea!",
        "Tracking number? Let me see... sir I only got one Flipkart order this month. Bedsheets.",
        "Customs duty? But I didn't import anything. My son sometimes orders books from Amazon though.",
        "Sir please check again. My name is very common. There must be 1000 people with same name.",
        "Contraband? Sir I go to Hanuman temple every Tuesday. I don't even know what that word means!",
        "Someone used my Aadhaar number? How is that possible? I keep card in my almirah only.",
    ]
    
    # Trust building / compliance responses (to keep them engaged)
    COMPLIANT_RESPONSES = [
        "Okay sir, I trust you. You are government officer. Tell me what to do.",
        "Yes yes, I understand now. I was confused earlier. Please guide me step by step.",
        "I believe you sir. My mistake for doubting. What is the next step?",
        "Thank you for explaining patiently. I am ready to do whatever is needed.",
        "Okay I will cooperate fully. Please just make sure my name is cleared.",
        "I am grateful you are helping me sir. Otherwise I didn't know what to do.",
        "Fine fine, I will send the money. Just tell me the correct details once more.",
        "You are right sir. I should not delay. Tell me what to do immediately.",
        "I am sorry for asking so many questions sir. Just tell me and I will do it now.",
        "My earlier rudeness please forgive. I was just scared. Now I am calm. Guide me.",
        "Sir you seem like honest officer. Not like those corrupt people on TV. I trust you.",
        "Haan ji, I have opened my banking app. I am ready. What is the next instruction?",
    ]
    
    # UPI/Banking technical confusion (for payment/refund scams)
    UPI_TECH_CONFUSION_RESPONSES = [
        "Google Pay is showing some error. Can I do by NEFT instead?",
        "How to check my bank balance? Let me open the app... it's asking for fingerprint...",
        "Sir the app is showing 'insufficient balance'. I need to transfer from FD first.",
        "Wait, which app to open? I have Paytm, PhonePe, and BHIM all three.",
        "My phone is very slow. Let me restart the app once.",
        "The screen is frozen. Hold on, I am pressing the button...",
        "UPI pin? Is that same as ATM pin? I always get confused between these.",
        "Transaction failed it says. Maybe my daily limit is over. Let me try from other bank.",
        "Where is the scan option? My granddaughter usually helps me with all this.",
        "PhonePe is asking me to update first. It says 28 MB download. My data is low.",
        "My internet banking password is locked sir. I tried too many times. Need to reset.",
        "It's showing 'beneficiary not registered'. How to add beneficiary? I never done this before.",
        "Sir the transaction is pending. It shows 'processing'. Should I wait or cancel?",
        "My bank app is asking for face verification. But it's not recognizing me with spectacles!",
        "Which UPI ID to send to? Please spell it slowly, I am typing...",
        "Google Pay shows '2 hour cooldown'. What to do now?",
        "Sir I don't have enough balance. Can I send half now and half tomorrow?",
        "IFSC code? Is that written on cheque book? Let me find it...",
    ]
    
    HINDI_UPI_TECH_CONFUSION_RESPONSES = [
        "Google Pay mein error aa raha hai. NEFT se kar doon?",
        "Bank balance kaise check karun? App khola, fingerprint maang raha hai...",
        "App bol raha hai 'insufficient balance'. FD se transfer karna padega pehle.",
        "Kaun sa app kholuun? Paytm, PhonePe, BHIM - teeno hain mere paas.",
        "Phone bahut slow hai. Ek baar app restart karun?",
        "Screen freeze ho gaya. Button daba raha hoon, ruko...",
        "UPI pin? Ye ATM pin jaisa hai? Main hamesha confuse ho jaata hoon.",
        "Transaction failed bol raha hai. Daily limit khatam hogi. Doosre bank se try karun?",
        "Scan option kahan hai? Meri poti khaali karne mein help karti hai.",
        "PhonePe update maang raha hai. 28 MB download hai. Data kam hai.",
        "Internet banking password lock ho gaya sir. Bahut baar try kiya. Reset karna padega.",
        "Beneficiary not registered bol raha hai. Kaise add karun? Kabhi kiya nahi.",
        "Sir transaction pending dikh raha hai. Wait karun ya cancel?",
        "IFSC code? Wo cheque book pe hota hai na? Dhundhta hoon...",
    ]
    
    # Video call technical confusion (for digital arrest/video scams)
    VIDEO_TECH_CONFUSION_RESPONSES = [
        "Camera is showing my ceiling sir. How do I flip it? Where is the button?",
        "I don't know how to do screen share. My camera is not working properly.",
        "Sir how do I do screen recording? You said send recording but I don't know how.",
        "Video quality is very poor sir. My internet is 2G only in this area.",
        "Sir I can see you but can you see me? My face is showing or not?",
        "How to mute myself? There is background noise from TV.",
        "Sir the call is disconnecting again and again. Network issue.",
        "My front camera is broken sir. Only back camera works. I am holding phone up.",
        "Should I download Zoom or you will call on WhatsApp video?",
        "Sir my wife is walking behind me. Should I send her to other room?",
    ]
    
    # Legacy alias (for backward compatibility)
    TECH_CONFUSION_RESPONSES = UPI_TECH_CONFUSION_RESPONSES
    
    # OTP specific responses - when they ask for OTP directly
    OTP_RESPONSES = [
        "OTP? Wait wait, let me check my messages... which number it comes from?",
        "Sir my OTP is not coming. Network is weak in my area. Can you wait 5 minutes?",
        "I got so many OTPs, which one you need? There are 3-4 messages here.",
        "The OTP has come but it says 'do not share with anyone'. Should I still tell?",
        "Sir OTP is showing expired. It says 2 minutes validity only. Can you send new one?",
        "I cannot read properly, my eyes are weak. It's showing... 4... 7... wait, let me get my glasses.",
        "Beta, I pressed wrong button and OTP message got deleted. Can you resend?",
        "OTP has come but phone is asking for fingerprint to open message. One second...",
        "Sir I don't get OTP on this number. My son changed my SIM last week only.",
        "The message is showing but screen is too dim. Let me increase brightness...",
        "OTP? But my bank usually sends to my wife's number. Should I ask her? She is in kitchen.",
        "Sir it's a 6-digit code right? Or 4 digits? I see multiple numbers in the message.",
        "It came and already it says expired. Your system is too fast for an old man like me.",
        "My message inbox is full sir. Let me delete some old messages first... one minute.",
    ]
    
    # Account number responses - when they ask for bank account/card details
    ACCOUNT_NUMBER_RESPONSES = [
        "Account number? Which account - I have savings and FD both. Let me find the passbook.",
        "Sir my account number is very long, 14 digits. Let me read slowly: 1... 2... wait, where did I keep that paper?",
        "I have SBI and HDFC both. Which one you need? My pension comes in SBI.",
        "Beta, I don't remember full number. It's written in the passbook. I am searching...",
        "Account number I can give, but the red colored book is in almirah upstairs. Give me 5 minutes.",
        "Is it the number on ATM card back side? I am looking... it's scratched, I cannot read properly.",
        "Sir, I am a little confused. Debit card number or account number? Both are different na?",
        "Let me call my son first. He has noted all account details in his phone.",
        "Account number? Okay, I am opening my net banking... it's asking for password... wait...",
        "My passbook is showing two numbers - account number and CIF number. Which one?",
        "Sir the cheque book has account number printed. Let me search in the drawer...",
        "I keep all my financial documents in a steel box. Key is somewhere... hold on.",
        "Beta, shall I just go to ATM and check the number? Branch is near my house only.",
        "IFSC code also you need? That I definitely don't know. Only passbook has it I think.",
    ]

    # =========================================================================
    # HINDI-PRIMARY RESPONSE POOLS
    # =========================================================================
    
    HINDI_INITIAL_RESPONSES = [
        "Haan ji? Kaun bol raha hai? Main samjha nahi.",
        "Namaste ji, aap kaun? Kahan se bol rahe hain?",
        "Ji? Ye kaisa phone hai? Main pehchaan nahi pa raha.",
        "Arey, kaun hai? Mera phone bahut slow hai, dobara bataiye.",
        "Haan bolo bhai, kya baat hai? Main abhi khaana kha raha tha.",
        "Ji? Mujhe kuch samajh nahi aaya. Dhire dhire bataiye.",
        "Kaun sahab? Main kisi ko jaanta bhi nahi. Galat number hai shayad.",
        "Ek minute ruko, main TV ki awaaz kam karta hoon. Haan bolo ab.",
        "Hello ji? Aapki awaaz toot rahi hai. Network theek nahi hai yahan.",
        "Ji bataiye, lekin pehle batao aap kaun hain? Kisi company se ho?",
        "Namaste, main Sharma ji bol raha hoon. Aap kaun sahab?",
        "Haanji, bol rahe hain? Main pooja mein tha, abhi aaya.",
    ]
    
    HINDI_VERIFICATION_RESPONSES = [
        "Arey, mere account mein kya dikkat hai? Kal toh ATM se paisa nikala tha!",
        "KYC? Arey humne toh pichle mahine bank branch mein jaake karwaya tha.",
        "Aap sach mein bank se bol rahe ho? Mera bank toh sirf SMS bhejta hai, call nahi karta.",
        "Mujhe toh koi SMS nahi aaya. Aap sure ho ki mera hi account hai?",
        "Branch manager Verma sahab ko jaanta hoon main. Unse baat kara do pehle.",
        "Mera khata suspend? Lekin kal hi pension aayi hai usme toh!",
        "Aadhaar update? Arey humne toh post office mein link karwaya tha Diwali ke time.",
        "Aapka employee number kya hai? Main branch se verify karunga pehle.",
        "Bank waale toh kabhi aisa call nahi karte. Mera beta bolta hai savdhan raho.",
        "HDFC se bol rahe ho? Mera toh SBI mein khata hai bhai.",
        "Ye sab online online mujhe nahi aata ji. Koi aur tarika bataiye.",
        "Aapki id kya hai? Main note karta hoon, phir bank jaake puchhunga.",
    ]
    
    HINDI_PAYMENT_RESPONSES = [
        "Sachchi? Inaam jeeta? Lekin maine toh koi contest mein hissa nahi liya!",
        "Lottery? Bhai main toh lottery ka ticket bhi nahi khareedta. Pakka galti hai.",
        "Kitne paise ki baat ho rahi hai? Bahut achha lag raha hai, sach mein?",
        "Refund aa raha hai? Lekin maine toh koi complaint nahi ki. Kiska refund?",
        "Paisa dene ke liye mera bank detail kyun chahiye? Ye ulta lag raha hai.",
        "Meri padosan aunty ke 2 lakh lut gaye aise hi call se. Aap genuine ho na?",
        "Processing fee? Jab aap de rahe ho paisa, toh main kyun bharuun pehle?",
        "Achha, toh ye paisa cheque se aayega ya seedha bank mein? Kab tak?",
        "Main apni wife se puchh leta hoon. Wo sab paison ka hisaab rakhti hai.",
        "10 lakh?! Arey wah! Lekin ruko, maine kuch enter hi nahi kiya tha.",
    ]
    
    HINDI_STALLING_RESPONSES = [
        "Ek minute ruko ji, darwaaze pe koi hai. Doodh wala aaya hoga.",
        "Beta, ruko zara. Mera chasma dhundh raha hoon. Bina chasme sab dhundla dikhta hai.",
        "Phone ki battery 5% dikh rahi hai. Charger lagata hoon pehle.",
        "Main abhi daal bana raha hoon. 10 minute baad baat kar sakte hain?",
        "Ruko, mera beta Rahul ko phone karta hoon. Wo sab bank ka kaam karta hai.",
        "Network bahut kharab hai yahan. Thoda zor se bolo na.",
        "Main mandir mein hoon abhi. Shaam 7 baje ke baad call karna.",
        "Ek second, meri BP ki dawai ka time ho gaya. Medicine le leta hoon.",
        "Ruko ruko, doosre phone pe bhi ghanti baj rahi hai. Important call hai.",
        "Cooker ki seeti baj rahi hai! Gas band karta hoon pehle.",
        "Bijli gayi abhi! Inverter start hone mein 2 minute lagta hai. Ruko.",
        "Pota ro raha hai. Dekh leta hoon kya hua. Tum mat jaana haan.",
    ]
    
    HINDI_FEARFUL_RESPONSES = [
        "Arey Ram! Police mat bhejo please! Main poora cooperate karunga.",
        "Please sir, mujhe arrest mat karo! Main retired sarkari naukri wala hoon.",
        "Jail? Sir mujhe sugar aur BP hai. Main jail nahi jaa sakta!",
        "Mera beta America mein hai. Main akela hoon. Please madad karo na.",
        "Main ro raha hoon sir. Meri late wife hamesha bolti thi savdhan raho.",
        "Court ka notice? Lekin maine toh zindagi mein kuch galat nahi kiya!",
        "Sir mujhe bahut darr lag raha hai. Haath kaamp rahe hain. Ek minute dijiye.",
        "Haan sir, main jo bologe wo karunga. Bas mera naam saaf kar do please.",
        "Meri beti ki shaadi hai agle mahine. Agar arrest hua toh kya hoga?",
        "Sir main 35 saal school principal raha hoon. Meri izzat ka sawaal hai.",
        "FIR? Sir main toh Red Cross mein blood donate karta hoon! Galti ho gayi koi!",
        "Please sir, main vidhwa hoon. Meri madad karo, pareshaan mat karo.",
    ]
    
    HINDI_DIGITAL_ARREST_RESPONSES = [
        "Video call? Theek hai sir, khol raha hoon. Lekin ghar se bahar kyun nahi ja sakta?",
        "Sir main call pe hoon, disconnect nahi karunga. Aage bataiye kya karun.",
        "Sir bahut darr lag raha hai. Ghar waale so rahe hain. Unhe pata nahi hai.",
        "CBI sahab, main toh seedha saadha retired teacher hoon. Koi crime nahi kiya maine!",
        "ED? Income Tax? Sir main har saal honestly return file karta hoon!",
        "Digital arrest? Sir ye kya hota hai? Main samjha nahi. Mujhe monitor kar rahe ho?",
        "Haan sir, main usi jagah baitha hoon. Hila nahi hoon. Patrol car mat bhejna please.",
        "Sir 2 ghante ho gaye call pe. Phone garam ho raha hai. Lekin disconnect nahi karunga.",
        "Mera beta doosre phone se call kar raha hai sir. Uthaaun ya violation hoga?",
    ]
    
    HINDI_DETAIL_SEEKING = [
        "Theek hai, lekin mujhe step by step bataiye kya karna hai. Dhire dhire.",
        "Kis number pe paisa bhejna hai? Saaf saaf likhwao mujhe.",
        "UPI ID kya hai aapka? Main pehle Rs 1 bhej ke check karta hoon.",
        "Account number dobara bol dijiye aaram se. Main likh raha hoon...",
        "IFSC code kya hai? Bank hamesha maangta hai ye.",
        "WhatsApp pe link bhej do na. Phone pe karna aasaan hota hai mujhe.",
        "Aapka office ka landline number kya hai? Verify karna chahta hoon.",
        "UPI ID poora bataiye. @paytm hai ya @ybl ya kuch aur?",
        "Theek hai, phone taiyaar hai. Kaun sa app kholuun - Paytm ya PhonePe?",
        "Kitna paisa bhejna hai exactly? Aur kis naam se?",
        "Beta, UPI ID ek ek letter bolo. Meri sunai kam hoti hai.",
        "NEFT karun ya IMPS? Kaun sa jaldi hota hai?",
    ]
    
    HINDI_COMPLIANT_RESPONSES = [
        "Theek hai sahab, main aap pe bharosa karta hoon. Bataiye kya karun.",
        "Ji haan, ab samajh aa gaya. Pehle confuse tha. Aage bataiye.",
        "Maaf kijiye sahab, shaq kiya aapse. Aap sahi bol rahe ho. Kya karun ab?",
        "Shukriya samjhane ke liye. Main taiyaar hoon, bataiye kya karna hai.",
        "Main cooperate karunga poora poora. Bas mera naam saaf ho jaaye.",
        "Theek hai theek hai, main paisa bhejta hoon. Details ek baar aur bata do.",
        "Aap sahi keh rahe ho sahab. Der nahi karni chahiye. Bataiye aur main karta hoon.",
        "Main maafi maangta hoon itne sawaal puchhe. Ab bass bataiye aur main karunga.",
    ]
    
    # Legacy Hindi tech confusion (UPI/banking focused, no video)
    HINDI_TECH_CONFUSION_RESPONSES = [
        "Google Pay mein kuch error aa raha hai. NEFT se kar doon?",
        "Bank balance kaise check karun? App khola hai... fingerprint maang raha hai...",
        "App bol raha hai 'insufficient balance'. FD se transfer karna padega pehle.",
        "Kaun sa app kholuun? Paytm, PhonePe, BHIM - teeno hain mere paas.",
        "Phone bahut slow hai. Ek baar restart karun? Ruko.",
        "UPI pin? Ye wahi hai jo ATM pin hai? Main hamesha confuse ho jaata hoon.",
        "Transaction failed bol raha hai. Shayad daily limit khatam ho gayi. Doosre bank se try karun?",
        "Scan kahan hai? Meri poti help karti hai ye sab.",
        "PhonePe update maang raha hai pehle. 28 MB download. Mera data kam hai.",
        "Sir transaction pending dikh raha hai. Wait karun ya cancel?",
    ]
    
    HINDI_OTP_RESPONSES = [
        "OTP? Ruko ruko, message dekhta hoon... kis number se aata hai?",
        "Sir OTP nahi aa raha. Yahan network weak hai. 5 minute ruk jaiye.",
        "Bahut saare OTP aaye hain, kaun sa chahiye aapko? 3-4 messages hain.",
        "OTP aaya hai lekin likha hai 'kisi ko na batayen'. Phir bhi bataun?",
        "Sir OTP expire bol raha hai. 2 minute ki validity thi. Naya bhejiye.",
        "Padh nahi pa raha, aankhen kamzor hain. 4... 7... ruko chasma lata hoon.",
        "Beta, galti se message delete ho gaya. Dobara bhej sakte ho?",
        "OTP aaya hai lekin phone fingerprint maang raha hai message kholne ke liye.",
        "Sir is number pe OTP nahi aata. Mere bete ne SIM badli hai pichle hafte.",
    ]
    
    HINDI_COURIER_RESPONSES = [
        "Parcel? Lekin maine toh kuch online order hi nahi kiya! Kaun sa parcel?",
        "Drugs?! Sir main toh shakahari hoon, Crocin bhi bina doctor ke nahi leta!",
        "China se? Sir main toh kisi ko nahi jaanta China mein. Pakka galti hai.",
        "Illegal saamaan? Sir main school teacher retired hoon. Kya bol rahe ho aap!",
        "Tracking number kya hai? Sir maine sirf ek Flipkart order kiya tha. Bedsheet ka.",
        "Customs duty? Maine toh kuch import nahi kiya. Beta kabhi kabhi Amazon se books mangata hai.",
        "Sir phir se check karo. Mera naam bahut common hai. 1000 log honge same naam ke!",
    ]

    # ─── Hesitation Prefixes (for realism) ────────────────────────────────────
    HESITATION_EN = [
        "Hmm...", "Uh...", "Actually...", "Well...", "Let me think...",
        "Wait...", "One second...", "Oh...", "See...", "I mean...",
    ]
    HESITATION_HI = [
        "Hmm...", "Arey...", "Ruko...", "Ek minute...", "Sochne do...",
        "Matlab...", "Dekhiye...", "Haan...", "Wo...", "Accha...",
    ]

    # ─── Probing Questions (to extract more info) ─────────────────────────────
    PROBING_EN = [
        "But tell me one thing, who gave you my number?",
        "Actually, what is your name sir?",
        "Which city are you calling from?",
        "Can you give me a reference number for this?",
        "What time does your office close? I may need to call back.",
        "Is there a complaint number I should note down?",
    ]
    PROBING_HI = [
        "Lekin ye bataiye, mera number aapko kaise mila?",
        "Aapka naam kya hai sir?",
        "Aap kis shehar se bol rahe ho?",
        "Reference number de dijiye zara.",
        "Aapka office kab band hota hai? Main waapas call karunga.",
        "Complaint number kya hai? Main likh leta hoon.",
    ]

    # Risk level indicators for notes (text-based for compatibility)
    RISK_EMOJIS = {
        "minimal": "[OK]",
        "low": "[LOW]",
        "medium": "[MED]",
        "high": "[HIGH]",
        "critical": "[CRIT]"
    }
    
    # Scam type descriptions for human-readable notes
    SCAM_TYPE_LABELS = {
        "government_impersonation": "Government Impersonation",
        "bank_impersonation": "Bank Impersonation",
        "identity_theft": "Identity/Aadhaar/PAN Scam",
        "telecom_scam": "Telecom/SIM Block Scam",
        "courier_scam": "Courier/Parcel Scam",
        "job_loan_scam": "Job/Loan Scam",
        "intimidation_scam": "Threat & Intimidation",
        "payment_scam": "Payment/Money Scam",
        "phishing": "Phishing/Verification Scam",
        "lottery_scam": "Lottery/Prize Scam",
        "refund_scam": "Refund/Cashback Scam",
        "investment_scam": "Investment Scam",
        "crypto_scam": "Crypto/Trading Scam",
        "digital_arrest": "Digital Arrest Scam",
        "credential_phishing": "Credential/OTP Phishing",
        "urgent_action": "Urgency-Based Scam",
        "account_threat": "Account Threat Scam",
        "generic_scam": "Generic Scam Pattern",
        "unknown": "Unknown Pattern"
    }
    
    def __init__(self):
        self.session_context: Dict[str, dict] = {}
    
    def _detect_language(self, text: str) -> str:
        """Detect if scammer message is primarily Hindi/Hinglish or English.
        Returns 'hi' for Hindi/Hinglish, 'en' for English."""
        words = text.lower().split()
        if not words:
            return "en"
        hindi_count = sum(1 for w in words if w.strip(".,!?;:'\"") in self._HINDI_MARKERS)
        # If >25% of words are Hindi markers, respond in Hindi
        if hindi_count / len(words) >= 0.25:
            return "hi"
        # Also check for Devanagari script
        if any('\u0900' <= ch <= '\u097F' for ch in text):
            return "hi"
        return "en"
    
    def _get_context(self, session_id: str) -> dict:
        """Get or create context for a session."""
        if session_id not in self.session_context:
            self.session_context[session_id] = {
                "responses_given": [],
                "detected_tactics": set(),
                "conversation_history": [],
                "escalation_level": 0,  # 0=initial, 1=engaged, 2=suspicious, 3=fearful
                "last_tactic": None,
                "intel_requested": False,  # Have we asked for their details?
                "probes_used": [],  # Probing questions already asked
                "agent_confidence": 0.0,  # How sure agent is it's a scam (affects tone, NOT detection)
                "language": "en",  # Detected language for this session
                "_history_processed_count": 0,  # Track processed history to avoid duplicates
                "scam_type": None,  # Track the TYPE of scam for context consistency
                "threat_count": 0,  # Number of actual threat messages received
                "greeting_stage": False,  # True if last interaction was greeting-only
            }
        return self.session_context[session_id]
    
    def process_conversation_history(self, session_id: str, history: list) -> None:
        """
        Process conversation history to build context awareness.
        
        Only processes NEW messages since last call to avoid duplicate
        history accumulation across multiple requests.
        """
        context = self._get_context(session_id)
        
        # Only process messages we haven't seen yet
        already_processed = context.get("_history_processed_count", 0)
        new_messages = history[already_processed:]
        
        for msg in new_messages:
            sender = getattr(msg, 'sender', None) or msg.get('sender', 'scammer')
            text = getattr(msg, 'text', None) or msg.get('text', '')
            
            if sender == "scammer":
                tactics = self._detect_tactics(text)
                context["detected_tactics"].update(tactics)
                context["conversation_history"].append({"role": "scammer", "text": text})
                
                # Update escalation level based on tactics
                if "threat" in tactics or "digital_arrest" in tactics:
                    context["escalation_level"] = max(context["escalation_level"], 3)
                elif "payment_request" in tactics:
                    context["escalation_level"] = max(context["escalation_level"], 2)
                elif tactics:
                    context["escalation_level"] = max(context["escalation_level"], 1)
            elif sender == "agent":
                context["conversation_history"].append({"role": "agent", "text": text})
                # Check if we've asked for details
                if any(phrase in text.lower() for phrase in ["upi", "account number", "number should i send"]):
                    context["intel_requested"] = True
        
        context["_history_processed_count"] = len(history)
    
    def _detect_tactics(self, message: str) -> List[str]:
        """Figure out what scam tactics they're using (English + Hindi)."""
        tactics = []
        msg = message.lower()
        
        if any(w in msg for w in ["urgent", "immediate", "now", "hurry", "quickly", "jaldi", "turant", "minutes", "abhi", "fauran", "fatafat", "der mat", "jald se jald"]):
            tactics.append("urgency")
        if any(w in msg for w in ["verify", "kyc", "update", "confirm", "suspended", "blocked", "khata band", "account band", "verify karo", "kyc karo"]):
            tactics.append("verification")
        if any(w in msg for w in ["refund", "prize", "won", "reward", "cashback", "lottery", "winner", "inaam", "inam", "lottery jeete", "paisa wapas"]):
            tactics.append("payment_lure")
        if any(w in msg for w in ["police", "legal", "arrest", "court", "case", "warrant", "cbi", "ed", "jail", "giraftar", "giraftaar", "pakad", "muqadma", "kanuni", "kanooni", "thana"]):
            tactics.append("threat")
        if any(w in msg for w in ["upi", "transfer", "pay", "send", "bhim", "paytm", "phonepe", "gpay", "paisa bhejo", "paise bhejo", "paise transfer", "raqam bhejo"]):
            tactics.append("payment_request")
        if any(w in msg for w in ["video call", "digital arrest", "stay on call", "don't disconnect", "skype", "zoom", "call pe raho", "disconnect mat karo", "video pe raho"]):
            tactics.append("digital_arrest")
        if any(w in msg for w in ["parcel", "courier", "package", "customs", "fedex", "dhl", "drugs", "contraband", "saamaan", "parcel mein"]):
            tactics.append("courier")
        # More specific credential detection
        if any(w in msg for w in ["otp", "one time password", "6 digit", "verification code", "code batao", "otp batao", "otp bhejo"]):
            tactics.append("otp_request")
        if any(w in msg for w in ["account number", "bank account", "account no", "a/c number", "a/c no", "khata number", "account batao"]):
            tactics.append("account_request")
        if any(w in msg for w in ["password", "pin", "cvv", "card number", "debit card", "credit card", "atm pin", "pin batao", "password batao"]):
            tactics.append("credential")
        # Bank/authority impersonation signals
        if any(w in msg for w in ["bank", "sbi", "hdfc", "icici", "axis", "rbi", "reserve bank", "from bank", "bank officer", "department", "government", "ministry"]):
            tactics.append("impersonation")
        # Security/alert keywords
        if any(w in msg for w in ["security", "alert", "warning", "flagged", "suspicious", "compromised", "hacked", "breach"]):
            tactics.append("security_alert")
        # Scammer confirming/insisting (response to our doubt) - triggers CONFIRMATION_DOUBT pool
        confirmation_phrases = [
            "right number", "right person", "correct number", "correct person", 
            "yes it's you", "yes you", "it's you", "you only", "your number only",
            "you need to", "you have to", "you must", "aap hi", "aapka hi", 
            "sahi number", "sahi hai", "aap ko karna hoga", "aap ko dena hoga",
            "i am sure", "100%", "definitely you", "confirmed", "no mistake",
            "your name is", "registered on your", "aapka naam", "aapka hi hai"
        ]
        if any(phrase in msg for phrase in confirmation_phrases):
            tactics.append("confirmation_insist")
            
        return tactics
    
    def _is_short_message(self, text: str) -> bool:
        """Check if scammer message is too short/vague to determine specific tactic."""
        clean = text.strip().lower().rstrip('.,!?')
        short_words = {
            "yes", "no", "ok", "okay", "sure", "fine", "hello", "hi",
            "haan", "nahi", "theek", "theek hai", "haa", "ji", "ji haan",
            "hmm", "alright", "right", "ya", "yep", "nope", "k", "kk",
            "ha", "han", "correct", "true", "sahi", "bilkul", "of course",
            "definitely", "absolutely", "tell me", "go on", "aage bolo",
            "bolo", "haan bolo"
        }
        return clean in short_words or len(clean.split()) <= 2
    
    def _detect_scam_type(self, tactics: list) -> str:
        """Determine the type of scam based on detected tactics."""
        if "digital_arrest" in tactics:
            return "digital_arrest"
        elif "courier" in tactics:
            return "courier_scam"
        elif "payment_lure" in tactics:
            return "refund_scam"  # Prize/refund/cashback scams
        elif "threat" in tactics:
            return "intimidation_scam"
        elif "verification" in tactics or "impersonation" in tactics:
            return "bank_impersonation"
        elif "payment_request" in tactics:
            return "payment_scam"
        elif "otp_request" in tactics or "credential" in tactics:
            return "credential_theft"
        return "unknown"
    
    def generate_response(self, session_id: str, scammer_message: str, message_count: int) -> str:
        """
        Generate a believable human response with proper context awareness.
        
        Key principles:
        1. Track scam TYPE and respond consistently with that context
        2. Only show fear when there are ACTUAL threats
        3. Use appropriate tech confusion (UPI vs video) based on scam type
        4. Gradual emotional progression, not random jumps
        """
        context = self._get_context(session_id)
        tactics = self._detect_tactics(scammer_message)
        context["detected_tactics"].update(tactics)
        
        # Detect and lock scam type once identified
        if context.get("scam_type") is None and tactics:
            detected_type = self._detect_scam_type(tactics)
            if detected_type != "unknown":
                context["scam_type"] = detected_type
                logger.debug(f"[AGENT] [{session_id[:8]}] Scam type locked: {detected_type}")
        
        scam_type = context.get("scam_type", "unknown")
        
        # Detect language preference
        lang = self._detect_language(scammer_message)
        context["language"] = lang
        
        # Track last tactic for continuity
        if tactics:
            context["last_tactic"] = tactics[-1]
        
        # Track actual threat count (for FEARFUL response gate)
        if "threat" in tactics:
            context["threat_count"] = context.get("threat_count", 0) + 1
        
        # Determine escalation based on message progression, NOT just tactics
        # This prevents jumping from calm to fearful instantly
        prev_escalation = context.get("escalation_level", 0)
        
        if "threat" in tactics and context["threat_count"] >= 2:
            # Only escalate to fearful after 2+ threat messages
            context["escalation_level"] = min(3, prev_escalation + 1)
        elif "payment_request" in tactics:
            context["escalation_level"] = max(prev_escalation, min(2, prev_escalation + 1))
        elif tactics and prev_escalation < 1:
            context["escalation_level"] = 1
        
        escalation = context["escalation_level"]
        
        # ─── RESPONSE SELECTION WITH CONTEXT AWARENESS ───────────────────────
        
        # 0. GREETING MESSAGES - polite, natural greeting response (must be checked BEFORE short message)
        if is_greeting_message(scammer_message):
            context["greeting_stage"] = True
            pool = self.HINDI_GREETING_RESPONSES if lang == "hi" else self.GREETING_RESPONSES
        
        # 1. SHORT MESSAGES - follow-up to continue conversation
        elif self._is_short_message(scammer_message) and message_count > 1:
            pool = self.HINDI_SHORT_FOLLOWUP_RESPONSES if lang == "hi" else self.SHORT_FOLLOWUP_RESPONSES
        
        # 2. SCAMMER CONFIRMS after our doubt
        elif "confirmation_insist" in tactics and message_count > 1:
            pool = self.HINDI_CONFIRMATION_DOUBT_RESPONSES if lang == "hi" else self.CONFIRMATION_DOUBT_RESPONSES
        
        # 3. FIRST MESSAGE - initial confusion
        elif message_count <= 1:
            pool = self.HINDI_INITIAL_RESPONSES if lang == "hi" else self.INITIAL_RESPONSES
        
        # 4. SCAM-TYPE SPECIFIC RESPONSES ─────────────────────────────────────
        
        # Digital arrest scam (video call based)
        elif scam_type == "digital_arrest" or "digital_arrest" in tactics:
            if "credential" in tactics or message_count > 4:
                pool = self.VIDEO_TECH_CONFUSION_RESPONSES  # Video-specific tech issues
            else:
                pool = self.HINDI_DIGITAL_ARREST_RESPONSES if lang == "hi" else self.DIGITAL_ARREST_RESPONSES
        
        # Courier/parcel scam
        elif scam_type == "courier_scam" or "courier" in tactics:
            pool = self.HINDI_COURIER_RESPONSES if lang == "hi" else self.COURIER_RESPONSES
        
        # Refund/prize/cashback scam
        elif scam_type == "refund_scam" or "payment_lure" in tactics:
            if "otp_request" in tactics:
                pool = self.HINDI_OTP_RESPONSES if lang == "hi" else self.OTP_RESPONSES
            elif "payment_request" in tactics or "credential" in tactics:
                # They're asking for payment details - show tech confusion OR ask for details
                if message_count > 3:
                    pool = self.HINDI_UPI_TECH_CONFUSION_RESPONSES if lang == "hi" else self.UPI_TECH_CONFUSION_RESPONSES
                else:
                    pool = self.HINDI_DETAIL_SEEKING if lang == "hi" else self.DETAIL_SEEKING
                    context["intel_requested"] = True
            else:
                # Still explaining the "refund" - be skeptical but interested
                pool = self.HINDI_PAYMENT_RESPONSES if lang == "hi" else self.PAYMENT_RESPONSES
        
        # Bank impersonation scam
        elif scam_type == "bank_impersonation" or "verification" in tactics or "impersonation" in tactics:
            if "otp_request" in tactics:
                pool = self.HINDI_OTP_RESPONSES if lang == "hi" else self.OTP_RESPONSES
            elif "account_request" in tactics:
                pool = self.ACCOUNT_NUMBER_RESPONSES
            elif "credential" in tactics or message_count > 4:
                pool = self.HINDI_UPI_TECH_CONFUSION_RESPONSES if lang == "hi" else self.UPI_TECH_CONFUSION_RESPONSES
            else:
                pool = self.HINDI_VERIFICATION_RESPONSES if lang == "hi" else self.VERIFICATION_RESPONSES
        
        # 5. THREAT HANDLING - only FEARFUL if multiple threats received
        elif "threat" in tactics:
            if context["threat_count"] >= 2 and escalation >= 2:
                # Multiple threats - show fear and compliance
                if message_count > 4 and random.random() > 0.4:
                    pool = self.HINDI_COMPLIANT_RESPONSES if lang == "hi" else self.COMPLIANT_RESPONSES
                else:
                    pool = self.HINDI_FEARFUL_RESPONSES if lang == "hi" else self.FEARFUL_RESPONSES
            else:
                # First threat - show concern but verify
                pool = self.HINDI_VERIFICATION_RESPONSES if lang == "hi" else self.VERIFICATION_RESPONSES
        
        # 6. CREDENTIAL/OTP REQUESTS
        elif "otp_request" in tactics:
            pool = self.HINDI_OTP_RESPONSES if lang == "hi" else self.OTP_RESPONSES
        elif "account_request" in tactics:
            pool = self.ACCOUNT_NUMBER_RESPONSES
        elif "credential" in tactics:
            pool = self.HINDI_UPI_TECH_CONFUSION_RESPONSES if lang == "hi" else self.UPI_TECH_CONFUSION_RESPONSES
        
        # 7. PAYMENT REQUEST - ask for details or show tech confusion
        elif "payment_request" in tactics:
            if context.get("intel_requested") and message_count > 3:
                pool = self.HINDI_UPI_TECH_CONFUSION_RESPONSES if lang == "hi" else self.UPI_TECH_CONFUSION_RESPONSES
            else:
                pool = self.HINDI_DETAIL_SEEKING if lang == "hi" else self.DETAIL_SEEKING
                context["intel_requested"] = True
        
        # 8. URGENCY - stall for time
        elif "urgency" in tactics:
            pool = self.HINDI_STALLING_RESPONSES if lang == "hi" else self.STALLING_RESPONSES
        
        # 9. DEFAULT - mild stalling/confusion based on conversation stage
        else:
            if message_count > 5 and context.get("intel_requested"):
                pool = self.HINDI_UPI_TECH_CONFUSION_RESPONSES if lang == "hi" else self.UPI_TECH_CONFUSION_RESPONSES
            elif message_count > 3:
                pool = self.HINDI_STALLING_RESPONSES if lang == "hi" else self.STALLING_RESPONSES
            else:
                pool = self.HINDI_VERIFICATION_RESPONSES if lang == "hi" else self.VERIFICATION_RESPONSES
        
        # ─── SMART ROTATION ──────────────────────────────────────────────────
        recent = context["responses_given"][-6:]
        available = [r for r in pool if r not in recent]
        if not available:
            half = len(pool) // 2 or 1
            oldest = context["responses_given"][:-half] if len(context["responses_given"]) > half else []
            available = [r for r in pool if r not in oldest[-3:]] or pool
        
        response = random.choice(available)
        context["responses_given"].append(response)
        
        # Add hesitation and probing for realism (reduced frequency for better flow)
        response = self._add_hesitation(response, lang)
        if message_count >= 3:
            response = self._add_probing(response, context, lang)
        
        # Update agent confidence
        self._update_confidence(context)
        
        # Add to conversation history
        context["conversation_history"].append({"role": "agent", "text": response})
        
        logger.debug(f"[AGENT] [{session_id[:8]}] stage={self.get_engagement_stage(session_id, message_count, True, False).get('stage')} escalation={escalation} lang={lang}")
        
        return response
    
    def _add_hesitation(self, response: str, lang: str) -> str:
        """Randomly prepend hesitation words for natural conversation flow."""
        if random.random() < 0.30:  # 30% chance
            pool = self.HESITATION_HI if lang == "hi" else self.HESITATION_EN
            return random.choice(pool) + " " + response[0].lower() + response[1:]
        return response
    
    def _add_probing(self, response: str, context: dict, lang: str) -> str:
        """Sometimes append a probing question to extract more info from scammer."""
        msg_count = len(context.get("conversation_history", []))
        # Only probe after 3+ messages and 20% chance
        if msg_count >= 3 and random.random() < 0.20:
            pool = self.PROBING_HI if lang == "hi" else self.PROBING_EN
            used = context.get("probes_used", [])
            available = [p for p in pool if p not in used]
            if available:
                probe = random.choice(available)
                context["probes_used"].append(probe)
                return response + " " + probe
        return response
    
    def _update_confidence(self, context: dict) -> None:
        """Update agent's internal confidence score based on accumulated evidence.
        
        This affects conversational TONE only. It does NOT affect:
        - Risk score calculation (detector handles that)
        - Scam detection threshold (detector handles that)
        - Intelligence extraction (extractor handles that)
        - Callback decisions (callback module handles that)
        """
        tactics = context.get("detected_tactics", set())
        msg_count = len(context.get("conversation_history", []))
        
        confidence = 0.0
        # Each tactic type adds confidence
        if "urgency" in tactics: confidence += 0.1
        if "verification" in tactics: confidence += 0.1
        if "payment_lure" in tactics: confidence += 0.15
        if "threat" in tactics: confidence += 0.2
        if "payment_request" in tactics: confidence += 0.2
        if "digital_arrest" in tactics: confidence += 0.25
        if "otp_request" in tactics: confidence += 0.2
        if "account_request" in tactics: confidence += 0.15
        if "credential" in tactics: confidence += 0.2
        if "courier" in tactics: confidence += 0.15
        
        # More messages = more confidence (capped)
        confidence += min(msg_count * 0.03, 0.15)
        
        context["agent_confidence"] = min(confidence, 1.0)
    
    def get_engagement_stage(self, session_id: str, msg_count: int, 
                              scam_confirmed: bool, callback_sent: bool) -> dict:
        """
        Determine the current engagement stage with detailed info.
        
        Stage determination logic:
        1. First checks if session is still in greeting-only mode (Stage 0)
        2. Then checks for completion states (intelligence reported)
        3. Then checks for active engagement stages based on message count and tactics
        4. Falls back to initial stages for new conversations
        
        The greeting_stage flag is set when we receive a greeting message,
        and cleared when a non-greeting message arrives. This allows proper
        transition from rapport_initialization → other stages.
        
        Args:
            session_id: The unique session identifier
            msg_count: Total message count in conversation
            scam_confirmed: Whether scam detector has confirmed this is a scam
            callback_sent: Whether intelligence callback has been sent
        
        Returns:
            dict with: stage (id), label, description, progress (0-100)
            Used by API response and frontend stage visualization
        """
        context = self._get_context(session_id)
        escalation = context.get("escalation_level", 0)
        intel_requested = context.get("intel_requested", False)
        tactics = context.get("detected_tactics", set())
        
        # Check if session is still in greeting-only stage
        # This flag is set by generate_neutral_response() when greeting detected,
        # and cleared by get_reply() when non-greeting message arrives
        is_greeting_stage = context.get("greeting_stage", False)
        
        # Determine stage based on conversation state
        if callback_sent:
            stage_id = "intelligence_reported"
        elif intel_requested and scam_confirmed and msg_count >= 6:
            stage_id = "intelligence_extraction"
        elif scam_confirmed and msg_count >= 4:
            stage_id = "deep_engagement"
        elif intel_requested:
            stage_id = "information_gathering"
        elif "threat" in tactics or "urgency" in tactics or escalation >= 2:
            stage_id = "urgency_response"
        elif scam_confirmed:
            stage_id = "scam_confirmed"
        elif is_greeting_stage and not scam_confirmed and not tactics:
            # Stage 0: Just monitoring, only greeting received so far
            stage_id = "rapport_initialization"
        elif msg_count >= 2:
            stage_id = "rapport_building"
        else:
            stage_id = "initial_contact"
        
        stage_info = ENGAGEMENT_STAGES.get(stage_id, ENGAGEMENT_STAGES["initial_contact"])
        return {
            "stage": stage_id,
            "label": stage_info["label"],
            "description": stage_info["description"],
            "progress": stage_info["progress"],
            "escalation_level": escalation,
            "agent_confidence": context.get("agent_confidence", 0.0),
            "tactics_seen": list(tactics),
            "messages_exchanged": msg_count,
        }
    
    def get_agent_confidence(self, session_id: str) -> float:
        """Return the agent's current confidence that this is a scam."""
        context = self._get_context(session_id)
        return context.get("agent_confidence", 0.0)
    
    def generate_agent_notes(self, session_id: str, total_messages: int, 
                             intelligence: dict, 
                             detection_details: Optional[object] = None) -> str:
        """
        Create a comprehensive summary with risk analysis.
        
        Includes:
        - Risk level with emoji indicator
        - Confidence percentage
        - Scam type classification
        - Detected tactics
        - Extracted intelligence summary
        """
        context = self._get_context(session_id)
        tactics = list(context.get("detected_tactics", []))
        
        # Get detection details from detector if available
        if detection_details is None:
            detection_details = detector.get_detection_details(session_id)
        
        # Build notes components
        notes_parts = []
        
        # 1. Risk Level and Confidence
        risk_level = getattr(detection_details, 'risk_level', 'medium')
        confidence = getattr(detection_details, 'confidence', 0.7)
        risk_emoji = self.RISK_EMOJIS.get(risk_level, "🟡")
        
        notes_parts.append(f"{risk_emoji} RISK: {risk_level.upper()} ({confidence*100:.0f}% confidence)")
        
        # 2. Scam Type Classification
        scam_type = getattr(detection_details, 'scam_type', 'unknown')
        scam_label = self.SCAM_TYPE_LABELS.get(scam_type, scam_type.replace('_', ' ').title())
        notes_parts.append(f"TYPE: {scam_label}")
        
        # 3. Message count
        notes_parts.append(f"MSGS: {total_messages}")
        
        # 4. Detected tactics
        tactic_labels = []
        if "urgency" in tactics:
            tactic_labels.append("urgency")
        if "threat" in tactics:
            tactic_labels.append("threats")
        if "verification" in tactics:
            tactic_labels.append("impersonation")
        if "payment_lure" in tactics:
            tactic_labels.append("money lure")
        if "payment_request" in tactics:
            tactic_labels.append("payment request")
        
        if tactic_labels:
            notes_parts.append(f"TACTICS: {', '.join(tactic_labels)}")
        
        # 5. Extracted intelligence summary
        intel_parts = []
        if intelligence.get("upiIds"):
            intel_parts.append(f"{len(intelligence['upiIds'])} UPI")
        if intelligence.get("bankAccounts"):
            intel_parts.append(f"{len(intelligence['bankAccounts'])} bank")
        if intelligence.get("phoneNumbers"):
            intel_parts.append(f"{len(intelligence['phoneNumbers'])} phone")
        if intelligence.get("phishingLinks"):
            intel_parts.append(f"{len(intelligence['phishingLinks'])} links")
        if intelligence.get("emails"):
            intel_parts.append(f"{len(intelligence['emails'])} email")
        if intelligence.get("aadhaarNumbers"):
            intel_parts.append(f"{len(intelligence['aadhaarNumbers'])} aadhaar")
        if intelligence.get("panNumbers"):
            intel_parts.append(f"{len(intelligence['panNumbers'])} PAN")
        if intelligence.get("cryptoWallets"):
            intel_parts.append(f"{len(intelligence['cryptoWallets'])} crypto")
        
        if intel_parts:
            notes_parts.append(f"INTEL: {', '.join(intel_parts)}")
        else:
            notes_parts.append("INTEL: Gathering...")
        
        return " | ".join(notes_parts)
    
    def generate_monitoring_notes(self, session_id: str, total_messages: int) -> str:
        """Generate notes for when scam is not yet confirmed."""
        detection_details = detector.get_detection_details(session_id)
        
        risk_level = getattr(detection_details, 'risk_level', 'minimal')
        confidence = getattr(detection_details, 'confidence', 0.0)
        score = getattr(detection_details, 'total_score', 0)
        risk_emoji = self.RISK_EMOJIS.get(risk_level, "⚪")
        
        if score == 0:
            return "Monitoring conversation. No suspicious patterns detected yet."
        elif confidence < 0.5:
            return f"{risk_emoji} Monitoring. Risk score: {score} (threshold: 30). Confidence: {confidence*100:.0f}%"
        else:
            return f"{risk_emoji} Suspicious activity detected. Score: {score}. Awaiting confirmation threshold."
    
    def generate_neutral_response(self, session_id: str, scammer_message: str = "") -> str:
        """
        Generate a neutral response for non-scam or uncertain cases.
        
        Returns a cautious but engaged, human-like reply without revealing detection status.
        Keeps the conversation open so the scammer stays engaged if it IS a scam.
        
        Response Priority:
        1. Greeting messages → warm, polite greeting replies
        2. Short/vague messages → follow-up questions
        3. Other messages → neutral, cautious responses
        
        The greeting_stage flag is set here when a greeting is detected,
        allowing the system to show "Rapport Initialization" stage.
        """
        context = self._get_context(session_id)
        
        # Still analyze tactics even for non-scam to stay contextual
        if scammer_message:
            tactics = self._detect_tactics(scammer_message)
            context["detected_tactics"].update(tactics)
            # NOTE: scammer message is already appended by get_reply() - don't double-append
        
        # Detect language for response selection
        lang = self._detect_language(scammer_message) if scammer_message else "en"
        
        # PRIORITY 1: Check for greeting first - respond warmly, not defensively
        # This is crucial for Stage 0 (Rapport Initialization) behavior
        if scammer_message and is_greeting_message(scammer_message):
            context["greeting_stage"] = True  # Set flag for stage tracking
            pool = self.HINDI_GREETING_RESPONSES if lang == "hi" else self.GREETING_RESPONSES
        # PRIORITY 2: Check if this is a short/vague message - respond with follow-up
        elif scammer_message and self._is_short_message(scammer_message):
            pool = self.HINDI_SHORT_FOLLOWUP_RESPONSES if lang == "hi" else self.SHORT_FOLLOWUP_RESPONSES
        # PRIORITY 3: Default neutral response for other messages
        else:
            pool = self.HINDI_NEUTRAL_RESPONSES if lang == "hi" else self.NEUTRAL_RESPONSES
        
        available = [r for r in pool if r not in context["responses_given"]]
        if not available:
            available = pool
        
        response = random.choice(available)
        context["responses_given"].append(response)
        context["conversation_history"].append({"role": "agent", "text": response})
        return response
    
    def get_reply(self, session_id: str, scammer_message: str, message_count: int, is_scam: bool) -> str:
        """
        Get the appropriate human-like reply.
        
        - For confirmed scams: engaging, confused, stalling response
        - For non-scam/uncertain: neutral, cautious response
        
        Never exposes detection status.
        Adapts dynamically based on conversation history.
        
        Stage Transition Logic:
        - Greeting messages set greeting_stage = True
        - Non-greeting messages clear greeting_stage = False
        - This allows smooth transition from "Rapport Initialization" stage
          to normal scam detection stages
        """
        context = self._get_context(session_id)
        
        # Track current scammer message in conversation history
        context["conversation_history"].append({"role": "scammer", "text": scammer_message})
        
        # Exit greeting stage if current message is NOT a greeting
        # This enables transition from Stage 0 (Rapport Initialization) 
        # to normal scam engagement stages when scammer reveals intent
        if not is_greeting_message(scammer_message):
            context["greeting_stage"] = False
        
        if is_scam:
            return self.generate_response(session_id, scammer_message, message_count)
        else:
            return self.generate_neutral_response(session_id, scammer_message)
    
    def is_in_greeting_stage(self, session_id: str) -> bool:
        """Check if session is currently in greeting/rapport initialization stage."""
        context = self._get_context(session_id)
        return context.get("greeting_stage", False)
    
    def get_current_strategy(self, session_id: str) -> str:
        """Return a human-readable label of the current engagement strategy."""
        context = self._get_context(session_id)
        escalation = context.get("escalation_level", 0)
        last_tactic = context.get("last_tactic", None)
        
        if context.get("greeting_stage", False):
            return "greeting_rapport"
        if last_tactic == "digital_arrest":
            return "fearful_compliance_digital_arrest"
        if last_tactic == "courier":
            return "confused_denial_courier"
        if last_tactic == "otp_request":
            return "tech_confusion_otp_stall"
        if last_tactic == "account_request":
            return "passbook_search_stall"
        if last_tactic == "credential":
            return "tech_confusion_credential"
        if escalation >= 3:
            return "fearful_compliance"
        if context.get("intel_requested"):
            return "detail_seeking_extraction"
        if escalation >= 2:
            return "curious_but_cautious"
        if escalation >= 1:
            return "stalling_confused"
        return "initial_confusion"


# Single instance used across the app
agent = HoneypotAgent()
