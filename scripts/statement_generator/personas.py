"""Five synthetic personas.

Every identity here is fictional. Account numbers, customer IDs and card
numbers are deliberately invalid (they fail standard checksums) so they can
never collide with a real account.

Personas vary by FINANCIAL SITUATION, not by bank. The demo needs to show the
analysis producing five different diagnoses, not five parsers.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class RecurringDebit:
    label: str          # internal category tag
    day: int            # day of month
    amount: int         # paise
    kind: str           # narration style: ach, emi, billpay, upi, neft, si
    counterparty: str


@dataclass
class SpendProfile:
    """Discretionary spending: category -> (times per month, min, max) in paise."""
    category: str
    per_month: float
    lo: int
    hi: int
    channel: str        # upi, pos, card
    merchants: list


@dataclass
class CardProfile:
    issuer: str
    product: str
    last4: str
    limit: int                      # paise
    statement_day: int
    due_day: int
    payment_style: Literal["full", "minimum", "partial"]
    spends: list = field(default_factory=list)


@dataclass
class Persona:
    key: str
    name: str
    address: list
    email: str
    phone: str
    cust_id: str
    account_no: str
    ifsc: str
    micr: str
    branch: str
    branch_address: list
    city: str
    state: str
    branch_code: str
    ac_open_date: str
    opening_balance: int            # paise
    income: list                    # list of (day, amount_paise, employer, variance_pct)
    recurring: list
    spends: list
    card: CardProfile
    narrative: str                  # what this persona is meant to demonstrate


R = 100  # rupees -> paise helper


def rs(x):
    return int(round(x * 100))


# --------------------------------------------------------------------------
# 1. Healthy saver — the "doing well" baseline
# --------------------------------------------------------------------------
ARJUN = Persona(
    key="arjun_salaried",
    name="MR. ARJUN MEHTA",
    address=["B/1204 SOBHA IVORY APARTMENTS", "OUTER RING ROAD, BELLANDUR",
             "OPP ECOSPACE TECH PARK", "BENGALURU 560103", "KARNATAKA INDIA"],
    email="ARJUN.MEHTA.DEMO@EXAMPLE.COM",
    phone="080-61606161",
    cust_id="71204483",
    account_no="50100299481736",
    ifsc="HDFC0000512",
    micr="560240031",
    branch="BELLANDUR - OUTER RING ROAD",
    branch_address=["SOBHA PEARL, GROUND FLOOR", "OUTER RING ROAD", "BELLANDUR"],
    city="BENGALURU 560103",
    state="KARNATAKA",
    branch_code="0512",
    ac_open_date="14/07/2019",
    opening_balance=rs(214_500),
    income=[(1, rs(172_400), "ZENTRIX LABS PVT LTD", 0)],
    recurring=[
        RecurringDebit("rent", 3, rs(38_000), "neft", "PRAKASH REDDY"),
        RecurringDebit("investment_sip", 5, rs(15_000), "si", "AXIS MF ELSS"),
        RecurringDebit("investment_sip", 5, rs(10_000), "si", "PARAG PARIKH FLEXI"),
        RecurringDebit("investment_ppf", 7, rs(12_500), "billpay", "PPF ACCOUNT"),
        RecurringDebit("insurance_term", 12, rs(2_180), "ach", "HDFC LIFE TERM"),
        RecurringDebit("insurance_health", 12, rs(1_950), "ach", "STAR HEALTH"),
        RecurringDebit("utilities", 8, rs(2_400), "billpay", "BESCOM"),
        RecurringDebit("utilities", 8, rs(1_100), "billpay", "ACT FIBERNET"),
        RecurringDebit("subscription", 14, rs(649), "upi", "NETFLIX"),
        RecurringDebit("subscription", 14, rs(199), "upi", "SPOTIFY"),
        RecurringDebit("loan_emi", 10, rs(31_600), "emi", "HOME LOAN"),
    ],
    spends=[
        SpendProfile("groceries", 4.0, rs(900), rs(3_400), "upi",
                     ["BIGBASKET", "ZEPTO", "MORE MEGASTORE", "NAMDHARIS FRESH"]),
        SpendProfile("food_delivery", 5.0, rs(240), rs(880), "upi",
                     ["SWIGGY", "ZOMATO"]),
        SpendProfile("dining", 2.0, rs(700), rs(2_600), "pos",
                     ["TOIT BREWPUB", "TRUFFLES", "CTR MALLESHWARAM"]),
        SpendProfile("transport", 6.0, rs(90), rs(520), "upi",
                     ["UBER INDIA", "OLA CABS", "NAMMA METRO"]),
        SpendProfile("shopping", 1.2, rs(1_100), rs(5_200), "card",
                     ["AMAZON IN", "MYNTRA", "DECATHLON"]),
        SpendProfile("health", 0.6, rs(400), rs(2_200), "upi",
                     ["APOLLO PHARMACY", "PRACTO", "CULT FIT"]),
    ],
    card=CardProfile(
        issuer="HDFC BANK", product="REGALIA GOLD CREDIT CARD", last4="4417",
        limit=rs(650_000), statement_day=18, due_day=8, payment_style="full",
        spends=[
            SpendProfile("shopping", 2.0, rs(1_400), rs(9_000), "card",
                         ["AMAZON IN", "CROMA", "MYNTRA", "IKEA BENGALURU"]),
            SpendProfile("dining", 2.5, rs(800), rs(3_600), "card",
                         ["TOIT BREWPUB", "SMOKE HOUSE DELI", "BLUE TOKAI"]),
            SpendProfile("travel", 0.5, rs(3_500), rs(22_000), "card",
                         ["INDIGO AIRLINES", "MAKEMYTRIP", "IRCTC"]),
            SpendProfile("fuel", 1.5, rs(1_200), rs(3_000), "card",
                         ["INDIAN OIL", "SHELL INDIA"]),
        ],
    ),
    narrative="Healthy saver. High savings rate, disciplined SIPs, adequate "
              "insurance, card paid in full monthly. Baseline for comparison.",
)

# --------------------------------------------------------------------------
# 2. Freelancer — irregular income
# --------------------------------------------------------------------------
MEERA = Persona(
    key="meera_freelance",
    name="MS. MEERA NAIR",
    address=["FLAT 7C, PALM MEADOWS", "17TH CROSS, INDIRANAGAR",
             "NEAR CMH ROAD", "BENGALURU 560038", "KARNATAKA INDIA"],
    email="MEERA.NAIR.DEMO@EXAMPLE.COM",
    phone="080-61606161",
    cust_id="66381902",
    account_no="50100177302948",
    ifsc="HDFC0000094",
    micr="560240012",
    branch="INDIRANAGAR - 100 FT ROAD",
    branch_address=["NO 2, 100 FEET ROAD", "HAL 2ND STAGE", "INDIRANAGAR"],
    city="BENGALURU 560038",
    state="KARNATAKA",
    branch_code="0094",
    ac_open_date="03/02/2017",
    opening_balance=rs(96_300),
    # Irregular: client invoices, variable timing and amount
    income=[
        (7, rs(85_000), "PIXELFORGE STUDIOS LLP", 45),
        (19, rs(62_000), "NORTHWIND CONSULTING", 60),
        (26, rs(38_000), "BRIGHTPATH MEDIA PVT LTD", 70),
    ],
    recurring=[
        RecurringDebit("rent", 4, rs(29_500), "neft", "SUDHA RAGHAVAN"),
        RecurringDebit("investment_sip", 8, rs(8_000), "si", "UTI NIFTY INDEX"),
        RecurringDebit("insurance_health", 15, rs(1_640), "ach", "NIVA BUPA"),
        RecurringDebit("utilities", 9, rs(1_800), "billpay", "BESCOM"),
        RecurringDebit("utilities", 9, rs(999), "billpay", "AIRTEL BROADBAND"),
        RecurringDebit("tax_advance", 15, rs(24_000), "billpay", "ADVANCE TAX"),
        RecurringDebit("subscription", 11, rs(1_770), "upi", "ADOBE CC"),
        RecurringDebit("subscription", 11, rs(649), "upi", "NETFLIX"),
    ],
    spends=[
        SpendProfile("groceries", 3.5, rs(700), rs(2_900), "upi",
                     ["ZEPTO", "BLINKIT", "SPAR HYPERMARKET"]),
        SpendProfile("food_delivery", 4.5, rs(220), rs(760), "upi",
                     ["SWIGGY", "ZOMATO"]),
        SpendProfile("dining", 2.5, rs(500), rs(2_100), "pos",
                     ["THIRD WAVE COFFEE", "GLENS BAKEHOUSE", "CHINITA"]),
        SpendProfile("transport", 7.0, rs(80), rs(600), "upi",
                     ["UBER INDIA", "RAPIDO", "NAMMA METRO"]),
        SpendProfile("business", 1.5, rs(900), rs(6_500), "card",
                     ["AWS INDIA", "CANVA", "WEWORK INDIA"]),
        SpendProfile("health", 0.5, rs(350), rs(1_800), "upi",
                     ["APOLLO PHARMACY", "CULT FIT"]),
    ],
    card=CardProfile(
        issuer="ICICI BANK", product="AMAZON PAY CREDIT CARD", last4="8823",
        limit=rs(280_000), statement_day=22, due_day=12, payment_style="full",
        spends=[
            SpendProfile("business", 1.5, rs(1_200), rs(7_500), "card",
                         ["AWS INDIA", "FIGMA", "NOTION LABS"]),
            SpendProfile("shopping", 1.5, rs(800), rs(5_500), "card",
                         ["AMAZON IN", "NYKAA"]),
            SpendProfile("travel", 0.3, rs(2_800), rs(15_000), "card",
                         ["INDIGO AIRLINES", "OYO ROOMS"]),
        ],
    ),
    narrative="Irregular income. Some months two client payments, some months "
              "none. Tests cash-flow volatility, advance tax, and whether the "
              "app can compute a meaningful savings rate without a fixed salary.",
)

# --------------------------------------------------------------------------
# 3. Revolving credit card debt — the distress case
# --------------------------------------------------------------------------
ROHIT = Persona(
    key="rohit_debt",
    name="MR. ROHIT BANSAL",
    address=["A/402 KUMAR PRIMAVERA", "RIVER RESIDENCY, WADGAON SHERI",
             "NEAR NAGAR ROAD", "PUNE 411014", "MAHARASHTRA INDIA"],
    email="ROHIT.BANSAL.DEMO@EXAMPLE.COM",
    phone="020-61606161",
    cust_id="59128744",
    account_no="50100133659021",
    ifsc="HDFC0000221",
    micr="411240015",
    branch="VIMAN NAGAR - PHOENIX",
    branch_address=["SHOP 4, NYATI EMPIRE", "NAGAR ROAD", "VIMAN NAGAR"],
    city="PUNE 411014",
    state="MAHARASHTRA",
    branch_code="0221",
    ac_open_date="19/11/2015",
    opening_balance=rs(18_900),
    income=[(1, rs(88_600), "MERIDIAN INFOTECH SERVICES", 0)],
    recurring=[
        RecurringDebit("rent", 2, rs(24_000), "neft", "ANIL KULKARNI"),
        RecurringDebit("loan_emi", 5, rs(14_800), "emi", "PERSONAL LOAN"),
        RecurringDebit("loan_emi", 7, rs(9_450), "emi", "TWO WHEELER LOAN"),
        RecurringDebit("card_payment", 9, rs(0), "billpay", "SBI CARDS"),      # computed
        RecurringDebit("card_payment", 21, rs(0), "billpay", "KOTAK CARDS"),   # computed
        RecurringDebit("utilities", 10, rs(1_950), "billpay", "MSEDCL"),
        RecurringDebit("utilities", 10, rs(799), "billpay", "JIO FIBER"),
        RecurringDebit("subscription", 16, rs(299), "upi", "HOTSTAR"),
    ],
    spends=[
        SpendProfile("groceries", 3.0, rs(600), rs(2_400), "upi",
                     ["DMART", "RELIANCE FRESH", "BLINKIT"]),
        SpendProfile("food_delivery", 6.0, rs(200), rs(700), "upi",
                     ["SWIGGY", "ZOMATO"]),
        SpendProfile("transport", 8.0, rs(60), rs(380), "upi",
                     ["RAPIDO", "UBER INDIA", "PUNE METRO"]),
        SpendProfile("cash_withdrawal", 1.5, rs(2_000), rs(6_000), "atm",
                     ["ATM WDL"]),
        SpendProfile("dining", 1.0, rs(400), rs(1_400), "pos",
                     ["CAFE GOODLUCK", "VAISHALI"]),
    ],
    card=CardProfile(
        issuer="SBI CARD", product="SIMPLYCLICK CREDIT CARD", last4="6602",
        limit=rs(180_000), statement_day=14, due_day=4, payment_style="minimum",
        spends=[
            SpendProfile("shopping", 2.5, rs(900), rs(6_800), "card",
                         ["AMAZON IN", "FLIPKART", "AJIO"]),
            SpendProfile("food_delivery", 3.0, rs(300), rs(1_100), "card",
                         ["SWIGGY", "ZOMATO"]),
            SpendProfile("fuel", 2.0, rs(1_000), rs(2_600), "card",
                         ["HP PETROL PUMP", "BHARAT PETROLEUM"]),
            SpendProfile("cash_advance", 0.25, rs(5_000), rs(15_000), "card",
                         ["CASH ADVANCE ATM"]),
        ],
    ),
    narrative="Revolving credit card debt. Pays only the minimum, so finance "
              "charges compound month over month. Two cards, one loan stack. "
              "This is the persona the app should flag most loudly.",
)

# --------------------------------------------------------------------------
# 4. Young saver — no cushion
# --------------------------------------------------------------------------
SNEHA = Persona(
    key="sneha_young",
    name="MS. SNEHA IYER",
    address=["2B, LAKSHMI APARTMENTS", "4TH STREET, BESANT NAGAR",
             "NEAR ELLIOTS BEACH", "CHENNAI 600090", "TAMIL NADU INDIA"],
    email="SNEHA.IYER.DEMO@EXAMPLE.COM",
    phone="044-61606161",
    cust_id="78440215",
    account_no="50100311772064",
    ifsc="HDFC0000318",
    micr="600240028",
    branch="BESANT NAGAR - ELLIOTS BEACH",
    branch_address=["NO 12, 2ND AVENUE", "BESANT NAGAR", "CHENNAI"],
    city="CHENNAI 600090",
    state="TAMIL NADU",
    branch_code="0318",
    ac_open_date="08/08/2024",
    opening_balance=rs(11_400),
    income=[(1, rs(54_200), "CALIBRE ANALYTICS PVT LTD", 0)],
    recurring=[
        RecurringDebit("rent", 3, rs(16_500), "neft", "LAKSHMI SUBRAMANIAN"),
        RecurringDebit("utilities", 8, rs(1_150), "billpay", "TNEB"),
        RecurringDebit("utilities", 8, rs(699), "billpay", "AIRTEL POSTPAID"),
        RecurringDebit("subscription", 12, rs(649), "upi", "NETFLIX"),
        RecurringDebit("subscription", 12, rs(119), "upi", "SPOTIFY"),
        RecurringDebit("subscription", 12, rs(299), "upi", "HOTSTAR"),
        RecurringDebit("subscription", 12, rs(499), "upi", "CULT FIT PASS"),
        RecurringDebit("family_transfer", 5, rs(8_000), "imps", "R IYER"),
    ],
    spends=[
        SpendProfile("food_delivery", 9.0, rs(180), rs(620), "upi",
                     ["SWIGGY", "ZOMATO", "SWIGGY INSTAMART"]),
        SpendProfile("dining", 3.5, rs(400), rs(1_800), "pos",
                     ["MURUGAN IDLI SHOP", "WRITERS CAFE", "STARBUCKS"]),
        SpendProfile("shopping", 2.5, rs(600), rs(4_200), "card",
                     ["MYNTRA", "NYKAA", "AMAZON IN", "ZUDIO"]),
        SpendProfile("transport", 9.0, rs(50), rs(320), "upi",
                     ["RAPIDO", "UBER INDIA", "CHENNAI METRO"]),
        SpendProfile("groceries", 1.5, rs(400), rs(1_600), "upi",
                     ["ZEPTO", "BLINKIT"]),
        SpendProfile("entertainment", 1.5, rs(300), rs(1_500), "upi",
                     ["BOOKMYSHOW", "PVR CINEMAS"]),
    ],
    card=CardProfile(
        issuer="AXIS BANK", product="MY ZONE CREDIT CARD", last4="9014",
        limit=rs(90_000), statement_day=25, due_day=15, payment_style="partial",
        spends=[
            SpendProfile("shopping", 3.0, rs(500), rs(4_000), "card",
                         ["MYNTRA", "NYKAA", "ZUDIO", "AMAZON IN"]),
            SpendProfile("dining", 2.0, rs(400), rs(1_600), "card",
                         ["STARBUCKS", "SOCIAL", "DOMINOS"]),
            SpendProfile("entertainment", 1.0, rs(300), rs(1_200), "card",
                         ["BOOKMYSHOW", "PVR CINEMAS"]),
        ],
    ),
    narrative="First job. No emergency fund, no term or health cover beyond "
              "employer group policy, seven active subscriptions, heavy food "
              "delivery. Card carries a partial balance most months.",
)

# --------------------------------------------------------------------------
# 5. Lifestyle creep — high income, thin savings
# --------------------------------------------------------------------------
VIKRAM = Persona(
    key="vikram_creep",
    name="MR. VIKRAM RAO",
    address=["1802, OBEROI SPLENDOR", "JVLR, ANDHERI EAST",
             "OPP MAJAS DEPOT", "MUMBAI 400060", "MAHARASHTRA INDIA"],
    email="VIKRAM.RAO.DEMO@EXAMPLE.COM",
    phone="022-61606161",
    cust_id="61903355",
    account_no="50100204918837",
    ifsc="HDFC0000060",
    micr="400240029",
    branch="ANDHERI EAST - JVLR",
    branch_address=["UNIT 3, SUPREME BUSINESS PARK", "JVLR", "ANDHERI EAST"],
    city="MUMBAI 400060",
    state="MAHARASHTRA",
    branch_code="0060",
    ac_open_date="27/05/2014",
    opening_balance=rs(147_800),
    income=[(1, rs(312_000), "HALCYON CAPITAL ADVISORS", 0)],
    recurring=[
        RecurringDebit("rent", 2, rs(115_000), "neft", "NILESH SHETH"),
        RecurringDebit("loan_emi", 5, rs(48_700), "emi", "CAR LOAN"),
        RecurringDebit("investment_sip", 6, rs(15_000), "si", "MIRAE LARGE CAP"),
        RecurringDebit("insurance_health", 13, rs(4_100), "ach", "TATA AIG"),
        RecurringDebit("utilities", 9, rs(6_800), "billpay", "ADANI ELECTRICITY"),
        RecurringDebit("utilities", 9, rs(1_499), "billpay", "TATA PLAY FIBER"),
        RecurringDebit("household_staff", 4, rs(18_000), "upi", "HOUSEHOLD HELP"),
        RecurringDebit("subscription", 15, rs(1_499), "upi", "APPLE ONE"),
        RecurringDebit("subscription", 15, rs(649), "upi", "NETFLIX PREMIUM"),
        RecurringDebit("club_membership", 20, rs(9_500), "ach", "FITNESS FIRST"),
    ],
    spends=[
        SpendProfile("dining", 6.0, rs(1_800), rs(9_500), "card",
                     ["THE TABLE", "BASTIAN", "YAUATCHA", "SOCIAL BKC"]),
        SpendProfile("groceries", 3.0, rs(2_200), rs(7_800), "upi",
                     ["NATURES BASKET", "FOODHALL", "ZEPTO"]),
        SpendProfile("transport", 10.0, rs(180), rs(900), "upi",
                     ["UBER INDIA", "BLUSMART"]),
        SpendProfile("shopping", 2.5, rs(3_500), rs(28_000), "card",
                     ["APPLE INDIA", "ZARA", "TATA CLIQ LUXURY"]),
        SpendProfile("travel", 0.7, rs(12_000), rs(65_000), "card",
                     ["VISTARA", "TAJ HOTELS", "MAKEMYTRIP"]),
        SpendProfile("fuel", 2.0, rs(2_500), rs(5_000), "card",
                     ["SHELL INDIA", "HP PETROL PUMP"]),
    ],
    card=CardProfile(
        issuer="KOTAK MAHINDRA BANK", product="WHITE RESERVE CREDIT CARD",
        last4="2077", limit=rs(1_200_000), statement_day=20, due_day=10,
        payment_style="partial",
        spends=[
            SpendProfile("dining", 4.0, rs(2_500), rs(12_000), "card",
                         ["BASTIAN", "THE TABLE", "MASQUE", "SODA BOTTLE"]),
            SpendProfile("travel", 0.8, rs(15_000), rs(85_000), "card",
                         ["VISTARA", "TAJ HOTELS", "EMIRATES", "MAKEMYTRIP"]),
            SpendProfile("shopping", 2.5, rs(4_000), rs(35_000), "card",
                         ["APPLE INDIA", "ZARA", "TATA CLIQ LUXURY", "CROMA"]),
            SpendProfile("fuel", 2.0, rs(2_500), rs(5_000), "card",
                         ["SHELL INDIA"]),
        ],
    ),
    narrative="High earner, thin savings rate. Rent and discretionary spending "
              "scaled with income. Large card balance carried at a low utilisation "
              "ratio, so it looks fine on the surface and is not.",
)


ALL_PERSONAS = [ARJUN, MEERA, ROHIT, SNEHA, VIKRAM]
BY_KEY = {p.key: p for p in ALL_PERSONAS}
