# ================================================================
# IEBS Tax & VAT Calculator Engine
# ================================================================

def calculate_income_tax(annual_income, gender='male', age=None, disabled=False, freedom_fighter=False):
    """ব্যক্তিগত আয়কর হিসাব ২০২৪-২৫"""
    
    # করমুক্ত সীমা নির্ধারণ
    if freedom_fighter:
        exemption = 500000
    elif disabled:
        exemption = 475000
    elif gender == 'female' or (age and age >= 65):
        exemption = 400000
    else:
        exemption = 350000
    
    taxable = max(0, annual_income - exemption)
    
    tax = 0
    breakdown = []
    remaining = taxable
    
    slabs = [
        (100000, 0.05, "পরবর্তী ১,০০,০০০"),
        (400000, 0.10, "পরবর্তী ৪,০০,০০০"),
        (500000, 0.15, "পরবর্তী ৫,০০,০০০"),
        (500000, 0.20, "পরবর্তী ৫,০০,০০০"),
        (float('inf'), 0.25, "অবশিষ্ট আয়"),
    ]
    
    for limit, rate, label in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, limit)
        tax_in_slab = taxable_in_slab * rate
        tax += tax_in_slab
        breakdown.append({
            'label': label,
            'amount': taxable_in_slab,
            'rate': f"{int(rate*100)}%",
            'tax': tax_in_slab
        })
        remaining -= taxable_in_slab
    
    # সর্বনিম্ন কর (ঢাকা/চট্টগ্রাম)
    min_tax = 5000 if annual_income > exemption else 0
    
    return {
        'annual_income': annual_income,
        'exemption': exemption,
        'taxable_income': taxable,
        'gross_tax': tax,
        'minimum_tax': min_tax,
        'final_tax': max(tax, min_tax) if taxable > 0 else 0,
        'monthly_tax': round(max(tax, min_tax) / 12) if taxable > 0 else 0,
        'breakdown': breakdown,
        'effective_rate': round((tax / annual_income * 100), 2) if annual_income > 0 else 0
    }

def calculate_rebate(investment_amount, annual_income):
    """বিনিয়োগ কর রেয়াত হিসাব"""
    max_investment = annual_income * 0.25
    eligible_investment = min(investment_amount, max_investment, 15000000)
    rebate = eligible_investment * 0.15
    max_rebate = 1000000
    final_rebate = min(rebate, max_rebate)
    return {
        'investment': investment_amount,
        'eligible_investment': eligible_investment,
        'rebate_rate': '১৫%',
        'rebate_amount': final_rebate,
        'max_investment_limit': max_investment
    }

def calculate_vat(price, rate=0.15, is_inclusive=False):
    """ভ্যাট হিসাব"""
    if is_inclusive:
        base_price = price / (1 + rate)
        vat_amount = price - base_price
    else:
        base_price = price
        vat_amount = price * rate
    
    return {
        'base_price': round(base_price, 2),
        'vat_rate': f"{int(rate*100)}%",
        'vat_amount': round(vat_amount, 2),
        'total_price': round(base_price + vat_amount, 2),
        'type': 'ভ্যাট অন্তর্ভুক্ত' if is_inclusive else 'ভ্যাট বহির্ভূত'
    }

def calculate_withholding(amount, payment_type):
    """উৎসে কর হিসাব"""
    rates = {
        'bank_interest': 0.10,
        'savings_certificate': 0.10,
        'contractor_supply': 0.07,
        'contractor_service': 0.05,
        'professional': 0.10,
        'export': 0.01,
        'rent_commercial': 0.30,
        'commission': 0.10,
        'dividend_listed': 0.20,
        'dividend_unlisted': 0.30,
        'salary': None,
    }
    
    labels = {
        'bank_interest': 'ব্যাংক সুদ',
        'savings_certificate': 'সঞ্চয়পত্র সুদ',
        'contractor_supply': 'ঠিকাদার (সরবরাহ)',
        'contractor_service': 'ঠিকাদার (সেবা)',
        'professional': 'পেশাদার সেবা',
        'export': 'রপ্তানি আয়',
        'rent_commercial': 'বাণিজ্যিক ভাড়া',
        'commission': 'কমিশন',
        'dividend_listed': 'লভ্যাংশ (তালিকাভুক্ত)',
        'dividend_unlisted': 'লভ্যাংশ (অন্যান্য)',
    }
    
    rate = rates.get(payment_type, 0.10)
    label = labels.get(payment_type, payment_type)
    tds = amount * rate
    
    return {
        'payment_type': label,
        'gross_amount': amount,
        'tds_rate': f"{int(rate*100)}%",
        'tds_amount': round(tds, 2),
        'net_amount': round(amount - tds, 2)
    }

def calculate_corporate_tax(profit, company_type='private'):
    """কোম্পানি আয়কর হিসাব"""
    rates = {
        'listed': 0.225,
        'private': 0.275,
        'bank': 0.40,
        'mobile': 0.45,
        'tobacco': 0.45,
        'garments': 0.12,
        'software': 0.00,
    }
    labels = {
        'listed': 'পাবলিক তালিকাভুক্ত কোম্পানি',
        'private': 'প্রাইভেট লিমিটেড কোম্পানি',
        'bank': 'ব্যাংক/বীমা/আর্থিক প্রতিষ্ঠান',
        'mobile': 'মোবাইল অপারেটর',
        'tobacco': 'তামাক কোম্পানি',
        'garments': 'গার্মেন্টস',
        'software': 'সফটওয়্যার/IT (শূন্য হার)',
    }
    rate = rates.get(company_type, 0.275)
    tax = profit * rate
    return {
        'company_type': labels.get(company_type, company_type),
        'net_profit': profit,
        'tax_rate': f"{int(rate*100)}%",
        'tax_amount': round(tax, 2),
        'after_tax_profit': round(profit - tax, 2)
    }

def calculate_import_duty(cif_value, cd_rate=0.25, sd_rate=0.0):
    """আমদানি শুল্ক হিসাব"""
    cd = cif_value * cd_rate
    rd = cif_value * 0.03  # Regulatory Duty (সাধারণ ৩%)
    vat_base = cif_value + cd + rd
    vat = vat_base * 0.15
    ait = cif_value * 0.05  # Advance Income Tax
    atv = vat_base * 0.04  # Advance Trade VAT
    sd = cif_value * sd_rate
    total = cif_value + cd + rd + sd + vat + ait + atv
    
    return {
        'cif_value': cif_value,
        'customs_duty': round(cd, 2),
        'regulatory_duty': round(rd, 2),
        'supplementary_duty': round(sd, 2),
        'vat': round(vat, 2),
        'advance_income_tax': round(ait, 2),
        'advance_trade_vat': round(atv, 2),
        'total_landed_cost': round(total, 2),
        'total_duty': round(total - cif_value, 2),
        'duty_percentage': round((total - cif_value) / cif_value * 100, 2)
    }

def parse_number(text):
    """Text থেকে সংখ্যা বের করো"""
    import re
    text = text.replace(',', '').replace('টাকা', '').replace('lakh', '00000').replace('লাখ', '00000').replace('লক্ষ', '00000').replace('কোটি', '0000000')
    nums = re.findall(r'\d+\.?\d*', text)
    if nums:
        return float(nums[0])
    return None

def detect_and_calculate(question):
    """প্রশ্ন থেকে calculation detect করো এবং হিসাব করো"""
    q = question.lower()
    result = None
    
    # আয়কর calculation
    if any(w in q for w in ['আয়কর হিসাব', 'কত কর', 'tax calculate', 'কত টাকা কর', 'আয়কর কত']):
        num = parse_number(question)
        if num:
            if num < 1000:  # লাখে দেওয়া
                num *= 100000
            gender = 'female' if any(w in q for w in ['মহিলা', 'নারী', 'female']) else 'male'
            result = {'type': 'income_tax', 'data': calculate_income_tax(num, gender)}
    
    # ভ্যাট calculation
    elif any(w in q for w in ['ভ্যাট হিসাব', 'vat calculate', 'ভ্যাট কত', 'vat কত']):
        num = parse_number(question)
        if num:
            inclusive = 'সহ' in q or 'inclusive' in q
            result = {'type': 'vat', 'data': calculate_vat(num, is_inclusive=inclusive)}
    
    # উৎসে কর
    elif any(w in q for w in ['উৎসে কর', 'tds', 'withholding']):
        num = parse_number(question)
        if num:
            ptype = 'professional'
            if 'সুদ' in q or 'interest' in q: ptype = 'bank_interest'
            elif 'ভাড়া' in q or 'rent' in q: ptype = 'rent_commercial'
            elif 'ঠিকাদার' in q or 'contractor' in q: ptype = 'contractor_service'
            result = {'type': 'withholding', 'data': calculate_withholding(num, ptype)}
    
    # কোম্পানি কর
    elif any(w in q for w in ['কর্পোরেট কর', 'company tax', 'কোম্পানির কর']):
        num = parse_number(question)
        if num:
            ctype = 'private'
            if 'তালিকাভুক্ত' in q or 'listed' in q: ctype = 'listed'
            elif 'ব্যাংক' in q: ctype = 'bank'
            elif 'গার্মেন্টস' in q: ctype = 'garments'
            result = {'type': 'corporate', 'data': calculate_corporate_tax(num, ctype)}
    
    # আমদানি শুল্ক
    elif any(w in q for w in ['আমদানি শুল্ক', 'import duty', 'customs duty হিসাব']):
        num = parse_number(question)
        if num:
            result = {'type': 'import_duty', 'data': calculate_import_duty(num)}
    
    return result

def format_calculation_result(calc_result):
    """Calculation result কে readable format-এ রূপান্তর করো"""
    if not calc_result:
        return ""
    
    ctype = calc_result['type']
    data = calc_result['data']
    
    def fmt(n):
        return f"৳{n:,.0f}"
    
    if ctype == 'income_tax':
        breakdown_text = ""
        for b in data['breakdown']:
            breakdown_text += f"\n  • {b['label']} ({b['rate']}): {fmt(b['tax'])}"
        
        return f"""
## 🧮 আয়কর হিসাব ফলাফল

| বিবরণ | পরিমাণ |
|-------|--------|
| মোট বার্ষিক আয় | {fmt(data['annual_income'])} |
| করমুক্ত সীমা | {fmt(data['exemption'])} |
| করযোগ্য আয় | {fmt(data['taxable_income'])} |
| **মোট কর** | **{fmt(data['final_tax'])}** |
| মাসিক কর (TDS) | {fmt(data['monthly_tax'])} |
| কার্যকর করহার | {data['effective_rate']}% |

**স্ল্যাব বিভাজন:**{breakdown_text}

> আইন: আয়কর আইন ২০২৩, প্রথম তফসিল"""

    elif ctype == 'vat':
        return f"""
## 🧮 ভ্যাট হিসাব ফলাফল ({data['type']})

| বিবরণ | পরিমাণ |
|-------|--------|
| মূল মূল্য | {fmt(data['base_price'])} |
| ভ্যাট হার | {data['vat_rate']} |
| ভ্যাটের পরিমাণ | {fmt(data['vat_amount'])} |
| **সর্বমোট মূল্য** | **{fmt(data['total_price'])}** |

> আইন: VAT ও SD আইন ২০১২, ধারা ১৫"""

    elif ctype == 'withholding':
        return f"""
## 🧮 উৎসে কর হিসাব ({data['payment_type']})

| বিবরণ | পরিমাণ |
|-------|--------|
| মোট পরিমাণ | {fmt(data['gross_amount'])} |
| উৎসে কর হার | {data['tds_rate']} |
| **কর্তনযোগ্য কর** | **{fmt(data['tds_amount'])}** |
| প্রাপক পাবেন | {fmt(data['net_amount'])} |

> আইন: আয়কর আইন ২০২৩, ধারা ৮৬-১৩৫"""

    elif ctype == 'corporate':
        return f"""
## 🧮 কোম্পানি আয়কর হিসাব

| বিবরণ | পরিমাণ |
|-------|--------|
| কোম্পানির ধরন | {data['company_type']} |
| নিট মুনাফা | {fmt(data['net_profit'])} |
| করহার | {data['tax_rate']} |
| **প্রদেয় কর** | **{fmt(data['tax_amount'])}** |
| কর পরবর্তী মুনাফা | {fmt(data['after_tax_profit'])} |

> আইন: আয়কর আইন ২০২৩, দ্বিতীয় তফসিল"""

    elif ctype == 'import_duty':
        return f"""
## 🧮 আমদানি শুল্ক হিসাব

| বিবরণ | পরিমাণ |
|-------|--------|
| CIF মূল্য | {fmt(data['cif_value'])} |
| কাস্টমস ডিউটি | {fmt(data['customs_duty'])} |
| Regulatory Duty | {fmt(data['regulatory_duty'])} |
| ভ্যাট | {fmt(data['vat'])} |
| অগ্রিম আয়কর (AIT) | {fmt(data['advance_income_tax'])} |
| অগ্রিম ট্রেড ভ্যাট | {fmt(data['advance_trade_vat'])} |
| **মোট শুল্ক** | **{fmt(data['total_duty'])}** |
| **মোট ল্যান্ডেড কস্ট** | **{fmt(data['total_landed_cost'])}** |
| শুল্ক শতাংশ | {data['duty_percentage']}% |

> আইন: Customs Act 2023"""

    return ""
