# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
# 
# Authors:
#   Xuqing Kuang <xkuang@redhat.com>

from tcms.management.models import Product

def pre_check_product(values):
    if isinstance(values, dict):
        if not values.get('product'):
            return
        product_str = values['product']
    else:
        product_str = values
    
    if not (isinstance(product_str, str) or isinstance(product_str, int)):
        raise ValueError('The type of product is not recognizable.')
    
    try:
        product_id = int(product_str)
        return Product.objects.get(id = product_id)
    except ValueError:
       return Product.objects.get(name = product_str)

def pre_process_ids(value):
    if isinstance(value, list):
        return [isinstance(c, int) and c or int(c.strip()) for c in value if c]
    
    if isinstance(value, str):
        return [int(c.strip()) for c in value.split(',') if c]
    
    if isinstance(value, int):
        return [value]
    
    raise TypeError('Unrecognizable type of ids')

def compare_list(src_list, dest_list):
    return list(set(src_list)-set(dest_list))
