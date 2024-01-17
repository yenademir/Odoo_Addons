from odoo import api

def get_suffix(line, partial_line):
    mapping = {
        'rawmaterial_line': "Raw Material",
        'cutting_line': "Cutting",
        'welding_line': "Welding",
        'coating_line': "Coating",
        'montage_line': "Montage",
    }

    abbreviations = {
        'rawmaterial_line': "R",
        'cutting_line': "C",
        'welding_line': "W",
        'coating_line': "Co",
        'montage_line': "M"
    }

    if partial_line:
        return [mapping[key] for key, value in mapping.items() if getattr(line, key)]
    else:
        return ''.join([abbreviations[key] for key, value in abbreviations.items() if getattr(line, key)])


def process_line(env, line, partial_line):
    Product = env['product.product']
    product_name_base = line.product_id.name
    suffixes = get_suffix(line, partial_line)

    products_to_add = []

    # If no suffixes are selected, directly add the base product to RFQ.
    if not suffixes:
        products_to_add.append(line.product_id)
        return products_to_add

    if partial_line:
        for suffix in suffixes:
            product_name = f"{product_name_base} {suffix}"
            product_to_add = Product.search([('name', '=', product_name)], limit=1)

            if not product_to_add:
                product_to_add = Product.create({'name': product_name})

            products_to_add.append(product_to_add)
    else:
        if suffixes:
            product_name = f"{product_name_base} {suffixes}"
            product_to_add = Product.search([('name', '=', product_name)], limit=1)

            if not product_to_add:
                product_to_add = Product.create({'name': product_name})

            products_to_add.append(product_to_add)

    return products_to_add
