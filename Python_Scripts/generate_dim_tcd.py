"""
Dim_TCD generator — ONE file only.
Creates Dim_TCD.csv in the sibling Data_Source folder.

Grain: one row = one hierarchy node.
  - 18 in-scope Top Contact Drivers (L1 products), each with L2/L3/L4
  - 42 additional catalog L1 products (out of 60 total), no drill-down
Level 1 = Product
Level 2 = Product sub-category
Level 3 = Contact reason
Level 4 = Contact reason detail
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Dim_TCD.csv"

# 18 in-scope Amazon retail CX products for this outsourced account.
IN_SCOPE = [
    {
        "l1": "Orders",
        "impact": "High",
        "prime": False,
        "financial": False,
        "l2": {
            "Place order": {
                "Order not going through": ["Payment declined at checkout", "Address validation fail", "Item out of stock at submit", "App crash on place order"],
                "Wrong item ordered": ["Incorrect variant selected", "Quantity mistake", "Gift-order mixup", "Voice-order error"],
                "Duplicate order": ["Double tap checkout", "Retry after timeout", "Family account overlap", "Subscribe-and-save clash"],
                "Order edit / cancel": ["Cancel window missed", "Item already shipped", "Partial cancel", "Address change after ship"],
            },
            "Order details": {
                "Missing order ID": ["Email not received", "Wrong account", "App filter hidden", "Shared household"],
                "Item missing on order": ["Seller delisted", "Split shipment", "Gift wrap line drop", "Add-on item drop"],
                "Wrong ASIN on order": ["Variant swap by seller", "Page content change", "Warehouse substitution", "Bundle component swap"],
                "Invoice / GST document": ["Invoice not generated", "GSTIN mismatch", "Need tax invoice", "Duplicate invoice"],
            },
            "Cancellations": {
                "Customer-initiated cancel": ["Changed mind", "Found better price", "Ordered by mistake", "Need different variant"],
                "Amazon-initiated cancel": ["Payment failure after confirm", "Seller cancelled", "Fraud review", "Inventory loss"],
                "Partial cancel": ["One item cancelled", "Quantity reduced", "Add-on removed", "Gift item cancelled"],
                "Cancel refund timing": ["Refund not started", "Wrong method", "Pending settlement", "Promo clawback"],
            },
            "Order confirmation": {
                "Confirmation not received": ["Email in spam", "SMS not sent", "App notification off", "Wrong phone on file"],
                "Wrong confirmation content": ["Wrong items listed", "Wrong delivery promise", "Wrong payment method shown", "Gift message missing"],
                "Need order copy": ["For bank / warranty", "For customs", "For workplace claim", "For gift recipient"],
                "Hold / review status": ["Payment review", "Address review", "Fraud challenge", "New-device login hold"],
            },
        },
    },
    {
        "l1": "Delivery and Tracking",
        "impact": "High",
        "prime": True,
        "financial": False,
        "l2": {
            "Tracking": {
                "Scan not updating": ["Stuck at fulfillment center", "Stuck at sortation", "No scan after out for delivery", "Carrier portal mismatch"],
                "Wrong tracking number": ["Relabelled package", "Merged shipment", "Carrier reuse of AWB", "App showing old AWB"],
                "Estimated delivery change": ["Promise slipped 1 day", "Promise slipped 3+ days", "Promise pulled earlier", "Weekend cutoff"],
                "Live map / driver": ["Map not available", "Driver circling", "OTP not shared", "Contact driver failed"],
            },
            "Delay": {
                "Missed promise": ["Prime next-day miss", "Same-day miss", "Standard miss", "Heavy-item miss"],
                "Weather / disruption": ["Rain delay", "Strike / capacity", "Festival surge", "Airport hold"],
                "Customer not available": ["No OTP", "Gate closed", "Wrong phone", "Safe-place not set"],
                "Customs / remote": ["Customs hold", "Remote pin-code", "Address incomplete", "ID required at door"],
            },
            "Failed delivery": {
                "Attempted not received": ["Card left, no parcel", "Neighbour handover", "Locker full", "False attempted scan"],
                "Returned to fulfillment": ["3 attempts exhausted", "Address rejected", "Customer refused", "COD cash issue"],
                "Damaged in transit": ["Box crushed", "Liquid leak", "Open-box seal break", "Weather damage"],
                "Mis-sort": ["Wrong route", "Wrong locker", "Wrong building", "Wrong city hub"],
            },
            "Delivery preference": {
                "Time slot": ["Need evening slot", "Need weekend", "Slot disappeared", "Slot charged extra"],
                "Leave at location": ["Safe place ignored", "Need gate code", "Need Amazon Key", "Do not leave"],
                "Amazon Locker / Hub": ["Locker full", "Code not working", "Hub closed", "Need locker change"],
                "Recipient change": ["Gift recipient", "Neighbour", "Office reception", "Family member OTP"],
            },
            "Proof of delivery": {
                "POD photo": ["Photo not of my door", "No photo captured", "Blurred photo", "Need photo copy"],
                "Signature / OTP": ["OTP not asked", "OTP asked twice", "Signed by unknown", "Need signed copy"],
                "Delivered but missing": ["Marked delivered, empty doorstep", "Wrong house photo", "Shared building", "Theft after scan"],
                "Age-restricted handoff": ["ID not checked", "ID rejected", "Minor in household", "Alcohol / pharmacy rule"],
            },
        },
    },
    {
        "l1": "Returns",
        "impact": "High",
        "prime": False,
        "financial": True,
        "l2": {
            "Start a return": {
                "Item not eligible": ["Window expired", "Final sale", "Hygiene seal broken", "Digital item"],
                "Wrong reason code": ["Need replacement not refund", "Need different size", "Need manufacturer warranty", "Need damaged-in-box"],
                "Label not generating": ["App error", "Weight mismatch", "Multi-item label", "International label"],
                "Quantity / partial": ["Return one of many", "Return accessory only", "Return gift item", "Return replacement unit"],
            },
            "Return status": {
                "Pickup not scheduled": ["No slot", "Slot cancelled", "Need self-ship", "Need drop-off point"],
                "Pickup missed": ["Agent no-show", "Customer missed", "Package not ready", "ID mismatch at pickup"],
                "In transit to FC": ["No scan after pickup", "Stuck at courier", "Received but not closed", "Lost return parcel"],
                "Return received not closed": ["Inspection pending", "Failed inspection", "Wrong item received", "Missing accessories"],
            },
            "Replacement": {
                "Replacement not shipped": ["Stock out", "Address hold", "Payment authorization", "Policy block"],
                "Wrong replacement sent": ["Wrong size", "Wrong colour", "Refurbished vs new", "Missing parts"],
                "Replacement delay": ["Longer than original promise", "Split from refund path", "Need to keep old unit", "Need advance replacement"],
                "Do not want replacement": ["Switch to refund", "Switch to repair", "Keep damaged + partial", "Cancel replacement"],
            },
            "Drop-off / pickup": {
                "Drop-off location": ["Store not accepting", "Hub closed", "Need different city", "QR not scanning"],
                "Packaging": ["Need polybag", "Need box", "Need invoice in parcel", "Need tamper seal"],
                "Prepaid vs self-ship": ["Need prepaid label", "Need self-ship reimbursement", "Weight limit", "Need extra label"],
                "Seller-fulfilled return": ["3P seller instructions", "Seller not responding", "Different courier", "Seller refused pickup"],
            },
        },
    },
    {
        "l1": "Refunds",
        "impact": "Critical",
        "prime": False,
        "financial": True,
        "l2": {
            "Refund status": {
                "Not initiated": ["Return closed but no refund", "Cancel closed but no refund", "Missing item refund pending", "Price adjustment pending"],
                "Pending with bank": ["Card refund lag", "UPI lag", "Net banking lag", "International card lag"],
                "Wrong amount": ["Promo clawback", "Partial item", "Shipping not included", "Gift-wrap not included"],
                "Wrong method": ["Went to original source", "Need Amazon Pay balance", "Need gift card", "Need bank account"],
            },
            "Refund method": {
                "Original payment": ["Card expired", "Card closed", "Wallet closed", "EMI already booked"],
                "Amazon Pay balance": ["Need instant credit", "Balance not visible", "Need transfer out", "Need statement"],
                "Gift card refund": ["GC not received", "GC amount wrong", "GC expired claim", "Need GC to another account"],
                "Bank transfer / NEFT": ["Need IFSC", "Failed NEFT", "Name mismatch", "Need another account"],
            },
            "Adjustments": {
                "Price match / drop": ["Item cheaper after buy", "Lightning deal miss", "Coupon not applied", "Subscribe discount miss"],
                "Shipping fee": ["Free-shipping miss", "Remote fee", "Weight correction", "Failed delivery fee"],
                "Promo / coupon": ["Coupon clawed back", "Prime promo miss", "Bank offer miss", "Cashback not posted"],
                "Goodwill": ["Delay gesture", "Damaged gesture", "Repeat-fail gesture", "Policy exception"],
            },
            "Charge issues": {
                "Charged twice": ["Duplicate capture", "Auth + capture confusion", "Replacement + original", "COD + prepaid"],
                "Charged after cancel": ["Late capture", "Seller charge", "Subscription renew", "Add-on leftover"],
                "EMI / pay-over-time": ["EMI not cancelled", "Foreclosure", "Interest question", "No-cost EMI miss"],
                "Gift card drain": ["GC used unexpectedly", "GC stolen claim", "Reload not showing", "Balance mismatch"],
            },
        },
    },
    {
        "l1": "Prime Membership",
        "impact": "High",
        "prime": True,
        "financial": True,
        "l2": {
            "Join / renew": {
                "Sign-up failed": ["Payment failed", "Already member", "Student verify fail", "Regional plan mismatch"],
                "Renewal surprise": ["Auto-renew charged", "Did not want annual", "Plan upgraded without consent", "Trial converted"],
                "Plan type": ["Monthly vs annual", "Student Prime", "Family / household", "Amazon Pay later bundle"],
                "Offer not applied": ["Prime day pre-req", "Bank offer", "New-customer promo", "Win-back offer"],
            },
            "Benefits": {
                "Delivery promise": ["Prime logo missing", "Speed not applied", "Item excluded", "Pin-code not Prime"],
                "Prime Video / Music": ["App not recognizing Prime", "Profile issue", "Device limit", "Catalog geo block"],
                "Exclusive deals": ["Deal not Prime-only as shown", "Lightning deal miss", "Early access miss", "Quantity limit"],
                "Other benefits": ["Prime Reading", "Free gaming / Twitch", "Photos storage", "Partner benefit"],
            },
            "Cancel / pause": {
                "Cancel not working": ["Button missing", "Refund rules", "Pause vs cancel", "Household member block"],
                "Refund on cancel": ["Prorate question", "Used benefits clawback", "Need goodwill", "Tax invoice on fee"],
                "Keep until period end": ["Need access till expiry", "Need Video only", "Need delivery only", "Need to turn off auto-renew"],
                "Win-back": ["Discount to stay", "Switch to monthly", "Student conversion", "Pause for N months"],
            },
            "Household": {
                "Add adult": ["Invite not received", "Limit reached", "Wrong email", "Teen vs adult"],
                "Remove member": ["Ex-member still charged", "Need data split", "Shared payment", "Prime Video profile leftover"],
                "Kids / teen": ["PIN", "Purchase approval", "Content filter", "Device login"],
                "Address / pin-code": ["Household address change", "Two cities", "Campus address", "Locker as default"],
            },
        },
    },
    {
        "l1": "Account and Login",
        "impact": "Critical",
        "prime": False,
        "financial": False,
        "l2": {
            "Sign-in": {
                "Password": ["Forgot password", "Reset link not received", "Reset loop", "New password rejected"],
                "OTP / 2FA": ["OTP not received", "OTP expired", "New device challenge", "Authenticator lost"],
                "Locked account": ["Too many attempts", "Fraud lock", "Unusual activity", "Need identity proof"],
                "Email / mobile change": ["Old email lost", "Old phone lost", "Both changed", "Need security approval"],
            },
            "Account takeover risk": {
                "Unrecognized order": ["Order I did not place", "Address I do not know", "Device I do not own", "Prime started by unknown"],
                "Unrecognized login": ["New city login", "New device", "Password changed", "Email changed"],
                "Compromised payment": ["Card added by unknown", "Gift card drained", "Refund diverted", "Amazon Pay sent out"],
                "Recovery": ["Need account restore", "Need order block", "Need payment freeze", "Need police / FIR letter"],
            },
            "Profile": {
                "Name / KYC": ["Need legal name change", "GSTIN profile", "Business vs personal", "Document reject"],
                "Communication": ["Stop emails", "Stop SMS", "Language", "Notification preferences"],
                "Addresses": ["Add address", "Delete address", "Default address", "Billing vs shipping"],
                "Close account": ["Need deletion", "Need data download", "Need seller unlink", "Need Prime end first"],
            },
            "Privacy / data": {
                "Personal data": ["Need data copy", "Need delete history", "Need browse-history wipe", "Need voice recording delete"],
                "Consent": ["Marketing consent", "Third-party share", "Ad personalization", "Alexa privacy"],
                "Documents": ["ID uploaded by mistake", "Need document purge", "Bank proof leftover", "Prescription leftover"],
                "Household privacy": ["Shared recommendations", "Shared lists", "Shared payment visibility", "Kids data"],
            },
        },
    },
    {
        "l1": "Payments and Amazon Pay",
        "impact": "Critical",
        "prime": False,
        "financial": True,
        "l2": {
            "Cards and UPI": {
                "Add payment method": ["Card not accepting", "UPI not linking", "Net banking missing", "International card"],
                "Failed charge": ["Insufficient funds", "Bank decline", "3DS fail", "Limit exceeded"],
                "Remove method": ["Card still charging", "Need default change", "Expired card", "Shared household card"],
                "Saved CVV / token": ["Need token delete", "Wallet token fail", "Click-to-pay", "One-time card"],
            },
            "Amazon Pay balance": {
                "Add money": ["Top-up failed", "Top-up pending", "Wrong amount", "Offer on top-up"],
                "Send money": ["P2P failed", "Wrong beneficiary", "Need reversal", "Limit"],
                "Pay at merchant": ["QR fail", "In-store decline", "Need refund from merchant", "Need receipt"],
                "Statement": ["Need ledger", "Need tax document", "Unrecognized debit", "Cashback not in ledger"],
            },
            "Gift cards": {
                "Redeem": ["Code not working", "Already redeemed", "Region lock", "Balance partial"],
                "Reload": ["Reload not posted", "Wrong account", "Need corporate GC", "Bulk codes"],
                "Balance": ["Balance missing", "Need transfer", "Expiry", "Need screenshot proof"],
                "Suspected misuse": ["Code stolen", "Balance drained", "Phishing site", "Need freeze"],
            },
            "COD and EMI": {
                "COD": ["COD not offered", "Need COD cancel", "Cash change", "COD charged prepaid"],
                "EMI conversion": ["Need convert to EMI", "No-cost EMI miss", "Foreclose", "EMI on cancelled order"],
                "Amazon Pay Later": ["Limit", "Repayment", "Late fee", "Need statement"],
                "Invoices": ["Need card charge invoice", "Need EMI invoice", "Need GST", "Need chargeback pack"],
            },
        },
    },
    {
        "l1": "Amazon Devices",
        "impact": "Medium",
        "prime": True,
        "financial": False,
        "l2": {
            "Echo / Alexa": {
                "Device setup": ["Wi-Fi join fail", "App not finding device", "Registration fail", "Need another household"],
                "Not responding": ["Wake word", "No sound", "Offline", "After outage"],
                "Privacy": ["Delete recordings", "Mute concern", "Camera / drop-in", "Kids skill"],
                "Accessory": ["Power adapter", "Battery pack", "Stand", "Need replacement unit"],
            },
            "Fire TV / Tablet": {
                "Setup": ["Remote pairing", "Account sign-in", "Wi-Fi", "Kids profile"],
                "Playback": ["Buffering", "App missing", "HDCP / 4K", "Surround sound"],
                "Remote / hardware": ["Remote lost", "Buttons dead", "Screen defect", "Warranty"],
                "Deregister": ["Gift the device", "Sold device", "Need factory reset help", "Still showing on account"],
            },
            "Kindle hardware": {
                "Setup": ["Register", "Wi-Fi", "Email-to-Kindle", "Storage full"],
                "Display": ["Dead pixels", "Touch fail", "Warm light", "Need replacement"],
                "Battery": ["Drain", "Not charging", "Swelling concern", "Cable"],
                "Warranty / repair": ["In warranty", "Out of warranty", "Accidental damage", "Need pickup"],
            },
            "Ring / other": {
                "Ring setup": ["Chime", "Subscription", "Shared users", "Video history"],
                "Eero / network": ["Mesh node", "ISP clash", "Guest network", "Outage"],
                "Warranty across devices": ["Serial not found", "Invoice needed", "Cross-country", "Refurbished unit"],
                "Recall / safety": ["Recall check", "Overheat", "Stop use advisory", "Replacement program"],
            },
        },
    },
    {
        "l1": "Kindle and Digital Content",
        "impact": "Medium",
        "prime": True,
        "financial": True,
        "l2": {
            "Purchase": {
                "Book not delivered": ["Not in library", "Wrong account", "Region catalog", "Pre-order not released"],
                "Wrong title": ["Sample vs full", "Edition mismatch", "Audiobook vs ebook", "Textbook version"],
                "Charged twice": ["Duplicate buy", "Family share charge", "Subscription plus buy", "Need refund"],
                "Promo": ["Kindle deal miss", "Prime Reading confusion", "Coupon", "Price drop after buy"],
            },
            "Reading": {
                "Download fail": ["Device full", "Whispersync", "Deregistered device", "App crash"],
                "Whispersync": ["Progress lost", "Notes lost", "Highlights mismatch", "Multi-device"],
                "Accessibility": ["Font", "Text-to-speech", "Dyslexic font", "Page turn"],
                "Remove / archive": ["Need remove from device", "Need hide from kids", "Need delete purchase", "Need share"],
            },
            "Kindle Unlimited / Reading": {
                "Borrow limit": ["Need return title", "Title left KU", "Waitlist", "Device not eligible"],
                "Billing": ["Unexpected renew", "Need cancel", "Need refund period", "Student plan"],
                "Catalog": ["Title missing", "Region missing", "Language", "Comics / magazines"],
                "Device eligibility": ["E-ink vs Fire", "Phone app", "Family library", "Household share"],
            },
            "Publishing / send-to-Kindle": {
                "Personal document": ["PDF not arriving", "File type rejected", "Size limit", "Conversion ugly"],
                "Email target": ["Need approved email", "Spam filter", "Wrong device target", "Need new address"],
                "Sideload": ["USB", "Calibre concern", "Format support", "DRM question"],
                "Library loan": ["Overdrive / Libby", "Loan expired", "Hold", "Country restrict"],
            },
        },
    },
    {
        "l1": "Prime Video",
        "impact": "Medium",
        "prime": True,
        "financial": True,
        "l2": {
            "Playback": {
                "Error code": ["Generic playback error", "Device not supported", "Too many streams", "Location / VPN"],
                "Quality": ["HD not available", "Buffering", "Audio sync", "Subtitles missing"],
                "Download": ["Download fail", "Expired download", "Device limit", "Need offline for travel"],
                "Live / sports": ["Start time", "Blackout", "Restart", "Score overlay"],
            },
            "Subscription": {
                "Channels / add-ons": ["Rent vs buy", "Channel not cancelled", "Free trial convert", "Need refund"],
                "Rent / buy title": ["Title missing after pay", "Wrong video quality paid", "Need re-download", "Need gift"],
                "Prime not recognized": ["Signed into wrong account", "Household", "App store mismatch", "Region"],
                "Parental": ["PIN", "Maturity", "Kids profile", "Purchase PIN"],
            },
            "Devices": {
                "Smart TV": ["App version", "Login code", "4K / HDR", "Remote"],
                "Fire TV": ["App missing", "Cache", "Recast", "Home theater"],
                "Mobile / web": ["Browser not supported", "Cast to TV", "Picture-in-picture", "Data usage"],
                "Deregister": ["Remove old TV", "Device limit", "Sold TV", "Need sign-out all"],
            },
            "Catalog / rights": {
                "Title disappeared": ["Licensing end", "Region", "Need expiry warning", "Need alternative"],
                "Language": ["Audio track", "Subtitle language", "Dub missing", "Original language"],
                "X-ray / extras": ["Bonus missing", "Trailer vs feature", "Episode order", "Season pass"],
                "Recommendation": ["Need reset taste", "Kids bleed into adult", "Watched still recommended", "Hidden title"],
            },
        },
    },
    {
        "l1": "Amazon Fresh and Grocery",
        "impact": "High",
        "prime": True,
        "financial": True,
        "l2": {
            "Availability": {
                "Slot": ["No slot", "Slot disappeared", "Need earlier slot", "Need night slot"],
                "Item OOS": ["Substitution offer", "Do not substitute", "Need similar brand", "Need cancel line"],
                "Pin-code": ["Fresh not serving", "Moved house", "Office vs home", "Need locker grocery"],
                "Minimum order": ["Basket below min", "Fee surprise", "Need coupon", "Need Prime check"],
            },
            "Quality": {
                "Expired / near expiry": ["Milk", "Produce", "Packaged", "Need photo proof"],
                "Damaged / melted": ["Cold chain", "Eggs", "Bread crush", "Leak"],
                "Wrong item": ["Substitution unwanted", "Wrong weight", "Wrong brand", "Missing freebie"],
                "Quantity": ["Short weight", "Missing unit", "Double unit charged", "Need weighment copy"],
            },
            "Delivery": {
                "Late slot": ["Missed window", "Need redelivery", "Need refund fee", "Need goodwill voucher"],
                "Partial bag": ["Some items pending", "Split delivery", "Need rest of basket", "Need cancel rest"],
                "OTP / handover": ["OTP not received", "Left at gate warm", "Need insulated bag", "Need contactless"],
                "Packaging": ["Ice pack missing", "Bag torn", "Need less plastic", "Need invoice in bag"],
            },
            "Refunds grocery": {
                "Item-level refund": ["Photo required", "Window short", "Partial weight", "Need instant credit"],
                "Whole order": ["Need full refund", "Need reorder", "Need fee refund", "Need tip / fee"],
                "Substitution price": ["Charged higher sub", "Need original price", "Need reject sub", "Need credit"],
                "Membership / pass": ["Fresh pass", "Delivery fee pass", "Need cancel pass", "Need refund pass"],
            },
        },
    },
    {
        "l1": "Fashion and Lifestyle",
        "impact": "Medium",
        "prime": False,
        "financial": False,
        "l2": {
            "Size / fit": {
                "Too small": ["Need size exchange", "Chart wrong", "Need tailor advice", "Need return"],
                "Too large": ["Need size exchange", "Chart wrong", "Kids size", "Need return"],
                "Length / rise": ["Kurta length", "Inseam", "Sleeve", "Need alteration policy"],
                "Try-and-buy": ["Slot", "Fee", "Item not in try list", "Need convert to buy"],
            },
            "Quality": {
                "Defect": ["Stitch", "Colour bleed", "Zipper", "Odour"],
                "Not as image": ["Colour", "Fabric", "Print", "Embellishment"],
                "Counterfeit concern": ["Brand authenticity", "Packaging", "Hologram", "Need brand letter"],
                "Care label": ["Missing label", "Wash instruction", "Allergen / metal", "Need replacement"],
            },
            "Exchange": {
                "Size exchange": ["Stock out of size", "Need different colour", "Need store drop", "Need prepaid"],
                "Wrong item received": ["Other customer item", "Wrong colour", "Missing pair", "Need instant reorder"],
                "Window": ["Exchange expired", "Festival window", "Need exception", "Need store credit"],
                "3P fashion seller": ["Seller policy stricter", "Seller not responding", "Need Amazon intervention", "Need A-to-z"],
            },
            "Jewellery / luxury": {
                "Authenticity": ["Certificate", "Hallmark", "Serial", "Need expert review"],
                "Insurance / value": ["Need invoice value", "Customs", "Need appraisal", "Need repair"],
                "Try at home": ["Programme question", "Pickup", "Need cancel trial", "Need convert"],
                "Return restriction": ["Hygiene / piercing", "Engraved", "Final sale", "Need exception"],
            },
        },
    },
    {
        "l1": "Gift Cards and Gifting",
        "impact": "High",
        "prime": False,
        "financial": True,
        "l2": {
            "Purchase GC": {
                "Not delivered": ["Email GC missing", "Print-at-home fail", "Need resend", "Wrong recipient email"],
                "Wrong amount": ["Need cancel", "Need top-up", "Need new code", "Need invoice"],
                "Corporate / bulk": ["Bulk order", "Need custom message", "Need GST invoice", "Need scheduled send"],
                "Payment on GC buy": ["Failed pay", "Double pay", "Need refund to source", "Need another method"],
            },
            "Redeem GC": {
                "Code reject": ["Already used", "Invalid format", "Region", "Currency"],
                "Partial balance": ["Need remaining balance", "Need another order", "Need merge", "Need expiry"],
                "Account mismatch": ["Redeemed to wrong account", "Need move balance", "Household", "Need proof"],
                "Suspect fraud": ["Phishing page", "Code asked on call", "Need freeze", "Need new code"],
            },
            "Physical gift": {
                "Gift wrap": ["Wrap missing", "Message card missing", "Wrong wrap", "Need invoice hidden"],
                "Gift receipt": ["Need price hidden", "Need return without giver", "Need exchange", "Need notify recipient"],
                "Delivery to recipient": ["Wrong address", "Surprise spoiled", "Need hold till date", "Need redirect"],
                "Registry": ["Wedding / baby", "Item purchased off registry", "Need thank-you list", "Need address privacy"],
            },
            "Balance and statements": {
                "Check balance": ["App vs code", "Need SMS balance", "Need expiry date", "Need transaction list"],
                "Transfer": ["Need move to another ID", "Not allowed", "Need exception", "Need cash out"],
                "Expired / fees": ["Expiry policy", "Need goodwill reload", "Need tax treatment", "Need invoice"],
                "Lost card": ["Physical card lost", "Need original receipt", "Need ID", "Need replacement code"],
            },
        },
    },
    {
        "l1": "Subscribe and Save",
        "impact": "Medium",
        "prime": True,
        "financial": True,
        "l2": {
            "Schedule": {
                "Change date": ["Need skip", "Need earlier", "Need pause", "Need date lock"],
                "Frequency": ["1 month vs 3", "Too frequent", "Too rare", "Need item-level freq"],
                "Quantity": ["Need increase", "Need decrease", "Need one-time extra", "Need cap"],
                "First delivery": ["Welcome discount", "Date too soon", "Need align dates", "Need combine box"],
            },
            "Discount": {
                "Percent missing": ["5% vs 15%", "Item count drop", "Need restore", "Need price lock"],
                "Price jump": ["Unit price up", "Need cancel", "Need match old price", "Need coupon stack"],
                "Coupon clash": ["Subscribe vs coupon", "Lightning vs subscribe", "Need one-time buy", "Need keep subscribe"],
                "Tax / fee": ["Fee added", "Need invoice", "Need GST", "Need shipping"],
            },
            "Manage items": {
                "Cancel item": ["Still shipped", "Need cancel next only", "Need cancel all", "Need keep discount"],
                "Swap item": ["Need different variant", "Need different brand", "Need larger pack", "Need scent"],
                "OOS": ["Skipped without notice", "Need substitute", "Need wait", "Need cancel"],
                "Address / payment": ["Need new address next drop", "Card failed", "Need retry", "Need skip on fail"],
            },
            "Unwanted shipment": {
                "Shipped after cancel": ["Need return", "Need refund", "Need stop next", "Need goodwill"],
                "Duplicate box": ["Two subscriptions", "Household overlap", "Need merge", "Need refund extra"],
                "Damaged consumable": ["Leak", "Expiry", "Need replace next date", "Need skip + credit"],
                "Gift / surprise": ["Need hide price", "Need change name", "Need stop emails", "Need recipient manage"],
            },
        },
    },
    {
        "l1": "Damaged Missing and Packaging",
        "impact": "High",
        "prime": False,
        "financial": True,
        "l2": {
            "Damaged on arrival": {
                "Box damage": ["Corner crush", "Open-box tape", "Wet box", "Need keep item or not"],
                "Item damage": ["Scratched", "Broken part", "Dented appliance", "Need photo steps"],
                "Used / returned look": ["Wrong slip inside", "Hair / dust", "Missing tags", "Need new sealed unit"],
                "Safety": ["Electrical concern", "Leak chemical", "Glass shatter", "Need disposal advice"],
            },
            "Missing from package": {
                "Entire item missing": ["Empty box", "Need investigation", "Need police note?", "Need advanced replacement"],
                "Accessory missing": ["Charger", "Cable", "Manual", "Spare bit"],
                "Multi-item shortage": ["1 of 3 missing", "Wrong count", "Need restock", "Need partial refund"],
                "Gift missing": ["Promo gift", "Sample", "Need honour promo", "Need substitute gift"],
            },
            "Wrong item in box": {
                "Different product": ["Need pickup both?", "Need keep + charge adjust", "Need urgent correct item", "Need seller claim"],
                "Different variant": ["Colour", "Size", "Storage / GB", "Region model"],
                "Dummy / stone": ["Security concern", "Need freeze account check", "Need investigation ID", "Need callback"],
                "Someone else order": ["PII in box", "Need privacy handling", "Need collect back", "Need notify other customer"],
            },
            "Packaging complaint": {
                "Overpack / waste": ["Too much plastic", "Need feedback log", "Need less air pillow", "Need paper mailer"],
                "Underpack": ["No protection", "Need extra packaging next", "Need fragile flag", "Need box not mailer"],
                "Invoice / slip": ["Invoice missing", "Invoice shows price on gift", "Need GST copy", "Need digital only"],
                "Label / PII": ["Label on inner item", "Name visible", "Need privacy pack", "Need remove sticker help"],
            },
        },
    },
    {
        "l1": "Marketplace Seller Issues",
        "impact": "High",
        "prime": False,
        "financial": True,
        "l2": {
            "Seller communication": {
                "No reply": ["Need Amazon step-in", "Need A-to-z path", "Need timeline", "Need call the seller"],
                "Wrong guidance": ["Seller asked extra pay", "Seller off-Amazon chat", "Seller warranty only", "Need official policy"],
                "Language / tone": ["Rude seller", "Spam links", "Need block seller", "Need record"],
                "Need Amazon mediation": ["Policy conflict", "Evidence pack", "Need deadline", "Need escalate"],
            },
            "A-to-z Guarantee": {
                "File claim": ["Button missing", "Window", "Need documents", "Need item not returned"],
                "Claim status": ["Pending", "Denied", "Need appeal", "Need more evidence"],
                "Claim amount": ["Partial grant", "Shipping not included", "Need tax", "Need goodwill top-up"],
                "Return for claim": ["Need label", "Seller refused return", "Need keep item", "Need photo only"],
            },
            "Listing accuracy": {
                "Not as described": ["Spec sheet wrong", "Country of origin", "Bundle contents", "Need price fairness"],
                "Counterfeit": ["Brand complaint", "Need authenticity check", "Need stop seller", "Need report brand"],
                "Condition": ["Used sold as new", "Open box", "Expired", "Need condition refund"],
                "Pricing": ["Sudden jump", "Hidden fee", "Need match Amazon-fulfilled", "Need cancel"],
            },
            "Fulfilled-by-seller logistics": {
                "Slow ship": ["SLA miss", "Need cancel", "Need Amazon-fulfilled alternative", "Need refund"],
                "No tracking": ["Need AWB", "Fake AWB", "Need investigation", "Need claim"],
                "Lost by seller courier": ["Need replacement", "Need refund", "Need police note?", "Need A-to-z"],
                "Return to seller": ["Different policy days", "Need prepaid", "Seller address far", "Need Amazon label"],
            },
        },
    },
    {
        "l1": "Amazon Pharmacy",
        "impact": "Critical",
        "prime": True,
        "financial": True,
        "l2": {
            "Prescription": {
                "Upload": ["Image reject", "Need new Rx", "Doctor details missing", "Need valid date"],
                "Verification": ["Pharmacist query", "Strength mismatch", "Quantity cap", "Controlled medicine"],
                "Consult": ["Need doctor consult", "Consult fee", "Need specialist", "Need follow-up Rx"],
                "Privacy": ["Rx on wrong account", "Need delete Rx image", "Family member Rx", "Need discreet pack"],
            },
            "Medicine order": {
                "Substitute": ["Generic vs brand", "Need same salt", "Need doctor approve sub", "Need reject sub"],
                "OOS": ["Need wait", "Need alternate seller", "Need local pharmacy advice", "Need cancel"],
                "Expiry": ["Near expiry", "Need longer dated", "Need return", "Need photo batch"],
                "Wrong medicine": ["Wrong salt", "Wrong strength", "Wrong form", "Safety stop"],
            },
            "Delivery pharmacy": {
                "Cold chain": ["Insulin warm", "Need replace", "Need disposal", "Need urgent redelivery"],
                "Discreet packaging": ["Invoice shows medicine", "Need plain pack", "Need hide from household", "Need locker"],
                "ID at door": ["Need age check", "OTP", "Someone else receive", "Need redelivery"],
                "Delay critical": ["Need local buy reimbursement", "Need escalate medical", "Need same-day", "Need cancel + refund"],
            },
            "Refund / insurance": {
                "Return policy": ["Opened strip", "Need exception", "Need destroy protocol", "Need credit"],
                "Price": ["MRP vs offer", "Need invoice for claim", "Need GST", "Need brand vs generic price"],
                "Insurance / FSA": ["Need itemized bill", "Need diagnosis not printed", "Need reimbursement letter", "Need pharmacy licence copy"],
                "Consult fee": ["Need refund consult", "Need second opinion", "Need attach to order", "Need invoice"],
            },
        },
    },
    {
        "l1": "App Website and Technical",
        "impact": "Medium",
        "prime": False,
        "financial": False,
        "l2": {
            "App": {
                "Crash": ["On launch", "On checkout", "On returns", "After update"],
                "Login in app": ["Biometric", "Saved password", "Force update", "Old OS"],
                "Notifications": ["Too many", "Not getting order alerts", "Need only delivery", "Need mute sales"],
                "Performance": ["Slow search", "Images not load", "Cart empty after refresh", "Need cache clear"],
            },
            "Website": {
                "Browser": ["Page blank", "Captcha loop", "Checkout button dead", "Need another browser"],
                "Search": ["Irrelevant results", "Filter stuck", "Need exact ASIN", "Need language"],
                "Account pages": ["Orders blank", "Returns blank", "Prime page error", "Need desktop vs mobile"],
                "Accessibility": ["Screen reader", "Keyboard", "Contrast", "Need help using site"],
            },
            "Cart and wishlist": {
                "Cart": ["Item vanished", "Saved for later", "Need share cart", "Need multiple carts"],
                "Wishlist": ["Need privacy", "Need move to cart", "Need delete", "Need gift pull"],
                "Recommendations": ["Need reset", "Need hide item", "Need stop recently viewed", "Need language catalog"],
                "Currency / country": ["Wrong store", ".in vs .com", "Need address country", "Need catalog switch"],
            },
            "Connectivity / device": {
                "Slow network": ["Need lite mode", "Need data warning", "Need retry", "Need desktop"],
                "OS / version": ["Android old", "iOS old", "Need APK concern", "Need web fallback"],
                "Clear cache": ["Need steps", "Lost cart after clear", "Need re-login", "Need saved cards"],
                "Security banner": ["Suspicious link", "Certificate warning", "Need official URL", "Need phishing check"],
            },
        },
    },
]

# 42 additional catalog products so the full Amazon TCD catalog = 60 L1s.
OUT_OF_SCOPE_L1 = [
    "Audible", "Amazon Music", "Amazon Photos", "Amazon Drive", "Twitch",
    "Amazon Luna", "Amazon Kids+", "Amazon Basics", "Amazon Renewed",
    "Amazon Warehouse", "Amazon Outlet", "Amazon Handmade", "Amazon Business",
    "Whole Foods", "Amazon Go", "Amazon Key", "Eero standalone",
    "Ring Alarm professional", "Amazon Pharmacy Pet", "Subscribe Beauty",
    "Amazon Custom", "Amazon Launchpad", "Amazon International Shopping",
    "Customs and Import Duty", "Student Prime verify", "Amazon Credit Card",
    "Amazon Store Card", "Shop with Points", "Amazon Smile legacy",
    "Amazon Charity", "Amazon Live", "Amazon Influencer", "Vine Voice",
    "Brand Registry customer side", "Amazon Haul", "Amazon Autos",
    "Amazon Air / freight delay", "Amazon Packaging feedback program",
    "Amazon Recycling / trade-in", "Amazon Warranty Services",
    "Amazon Protect", "Alexa for Residential",
]


def slug(text, prefix, n):
    return f"{prefix}-{n:02d}"


def impact_for_reason(l1_impact, l3, l4):
    text = f"{l3} {l4}".lower()
    if any(k in text for k in ["fraud", "takeover", "counterfeit", "wrong medicine", "privacy", "dummy", "stolen"]):
        return "Critical"
    if any(k in text for k in ["refund", "charged twice", "missing", "damaged", "a-to-z", "otp"]):
        return "High"
    return l1_impact


def copq_hint(financial, l3, l4):
    text = f"{l3} {l4}".lower()
    if any(k in text for k in ["privacy", "pII", "data", "prescription", "takeover"]):
        return "COP-PR"
    if any(k in text for k in ["fraud", "counterfeit", "wrong medicine", "safety"]):
        return "COP-FT"
    if financial or "refund" in text or "charged" in text:
        return "COP-RS"
    if "rude" in text or "tone" in text:
        return "COP-SS"
    return "COP-DC"


def quality_focus(l1, l3, l4):
    text = f"{l1} {l3} {l4}".lower()
    if any(k in text for k in ["privacy", "login", "otp", "kyc", "prescription"]):
        return "Authentication / Compliance"
    if any(k in text for k in ["refund", "charge", "emi", "gift card"]):
        return "Resolution / SOP"
    if any(k in text for k in ["delay", "missing", "damaged", "not received"]):
        return "Resolution / SOP"
    if any(k in text for k in ["rude", "tone", "empathy"]):
        return "Soft Skills"
    return "Process / Discovery"


def build_dim_tcd():
    rows = []
    l1_code_n = 0

    for item in IN_SCOPE:
        l1_code_n += 1
        l1 = item["l1"]
        l1_code = slug(l1, "TCD", l1_code_n)
        l2_n = 0
        for l2, reasons in item["l2"].items():
            l2_n += 1
            l2_code = f"{l1_code}-S{l2_n:02d}"
            l3_n = 0
            for l3, details in reasons.items():
                l3_n += 1
                l3_code = f"{l2_code}-R{l3_n:02d}"
                l4_n = 0
                for l4 in details:
                    l4_n += 1
                    l4_code = f"{l3_code}-D{l4_n:02d}"
                    impact = impact_for_reason(item["impact"], l3, l4)
                    rows.append(
                        {
                            "TcdLeafKey": l4_code,
                            "TcdL1Code": l1_code,
                            "TcdL2Code": l2_code,
                            "TcdL3Code": l3_code,
                            "TcdL4Code": l4_code,
                            "Level1Product": l1,
                            "Level2SubCategory": l2,
                            "Level3ContactReason": l3,
                            "Level4ReasonDetail": l4,
                            "HierarchyPath": f"{l1} > {l2} > {l3} > {l4}",
                            "HierarchyDepth": 4,
                            "IsTopDriver": True,
                            "IsInScope": True,
                            "IsActive": True,
                            "ImpactTier": impact,
                            "IsPrimeRelated": item["prime"],
                            "IsFinancial": item["financial"] or ("refund" in l3.lower()) or ("charge" in l4.lower()),
                            "IsComplianceSensitive": any(
                                k in f"{l1} {l3} {l4}".lower()
                                for k in ["privacy", "login", "otp", "kyc", "prescription", "takeover", "fraud", "pharmacy"]
                            ),
                            "IsComplaint": any(
                                k in f"{l3} {l4}".lower()
                                for k in ["missing", "damaged", "delay", "wrong", "not received", "charged twice", "counterfeit"]
                            ),
                            "RepeatContactRisk": "High" if impact in {"Critical", "High"} else "Medium",
                            "TypicalAhtSec": {"Critical": 780, "High": 620, "Medium": 480, "Low": 360}[impact],
                            "DefaultChannelMix": "Voice,Chat",
                            "CopqClassHint": copq_hint(item["financial"], l3, l4),
                            "QualityFocusAttribute": quality_focus(l1, l3, l4),
                            "CatalogTcdCount": 60,
                            "InScopeTcdCount": 18,
                        }
                    )

    for name in OUT_OF_SCOPE_L1:
        l1_code_n += 1
        l1_code = slug(name, "TCD", l1_code_n)
        rows.append(
            {
                "TcdLeafKey": l1_code,
                "TcdL1Code": l1_code,
                "TcdL2Code": "",
                "TcdL3Code": "",
                "TcdL4Code": "",
                "Level1Product": name,
                "Level2SubCategory": "",
                "Level3ContactReason": "",
                "Level4ReasonDetail": "",
                "HierarchyPath": name,
                "HierarchyDepth": 1,
                "IsTopDriver": False,
                "IsInScope": False,
                "IsActive": False,
                "ImpactTier": "Low",
                "IsPrimeRelated": False,
                "IsFinancial": False,
                "IsComplianceSensitive": False,
                "IsComplaint": False,
                "RepeatContactRisk": "Low",
                "TypicalAhtSec": 0,
                "DefaultChannelMix": "",
                "CopqClassHint": "",
                "QualityFocusAttribute": "",
                "CatalogTcdCount": 60,
                "InScopeTcdCount": 18,
            }
        )

    df = pd.DataFrame(rows)

    # Mix weights only on in-scope leaves, sum to 1.0 for later TCD mix-shift.
    in_scope = df["IsInScope"] & (df["HierarchyDepth"] == 4)
    l1_share = df.loc[in_scope].groupby("Level1Product").size()
    raw = 1.0 / l1_share
    df["MixWeightHint"] = 0.0
    df.loc[in_scope, "MixWeightHint"] = df.loc[in_scope, "Level1Product"].map(lambda p: (1.0 / 18) / l1_share[p])
    df["SortOrder"] = range(1, len(df) + 1)
    return df


def main():
    np.random.seed(SEED)
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    dim = build_dim_tcd()
    l1_in = dim.loc[dim["IsInScope"], "Level1Product"].nunique()
    l1_all = dim["Level1Product"].nunique()
    if l1_all != 60:
        raise ValueError(f"Expected 60 L1 products, got {l1_all}")
    if l1_in != 18:
        raise ValueError(f"Expected 18 in-scope L1, got {l1_in}")
    dim.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("Rows:", len(dim))
    print("L1 catalog:", l1_all, "| in-scope L1:", l1_in)
    print("In-scope L4 leaves:", int((dim["HierarchyDepth"] == 4).sum()))
    print("Out-of-scope L1 stubs:", int((~dim["IsInScope"]).sum()))
    print("Mix weight sum (leaves):", round(dim.loc[dim["HierarchyDepth"] == 4, "MixWeightHint"].sum(), 4))


if __name__ == "__main__":
    main()