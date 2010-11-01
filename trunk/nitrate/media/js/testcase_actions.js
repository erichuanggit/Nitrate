Nitrate.TestCases = {};
Nitrate.TestCases.List = {};
Nitrate.TestCases.Details = {};
Nitrate.TestCases.Create = {};
Nitrate.TestCases.Edit = {};
Nitrate.TestCases.Clone = {};

Nitrate.TestCases.List.on_load = function()
{
    bind_category_selector_to_product(true, true, $('id_product'), $('id_category'));
    bind_component_selector_to_product(true, true, $('id_product'), $('id_component'));
    if($('id_checkbox_all_case')) {
        $('id_checkbox_all_case').observe('click', function(e) {
            clickedSelectAll(this, this.up(4), 'case')
        });
    };
    if($('testcases_table')) {
        TableKit.Sortable.init('testcases_table',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'
        });
    };

}

Nitrate.TestCases.Details.on_load = function()
{
    var case_id = Nitrate.TestCases.Instance.pk;
    constructTagZone('tag', { 'case': case_id });
    constructPlanCaseZone($('plan'), case_id);
    $$('li.tab a').invoke('observe', 'click', function(i) {
        $$('div.tab_list').invoke('hide');
        $$('li.tab').invoke('removeClassName', 'tab_focus');
        this.parentNode.addClassName('tab_focus');
        $(this.title).show();
    });
    $('id_update_component').observe('click', function(e) {
        if(this.diabled)
        return false;
        
        var params = {
            'case': Nitrate.TestCases.Instance.pk,
            'product': Nitrate.TestCases.Instance.product_id,
            'category': Nitrate.TestCases.Instance.category_id,
            // 'component': 
        };
        
        var form_observe = function(e) {
            e.stop();
            
            var params = this.serialize(true);
            params['case'] = Nitrate.TestCases.Instance.pk
            
            var url = getURLParam().url_cases_component;
            var success = function(t) {
                returnobj = t.responseText.evalJSON(true);
                
                if (returnobj.rc == 0) {
                    window.location.reload();
                } else {
                    alert(returnobj.response);
                    return false;
                }
            }
            
            new Ajax.Request(url, {
                method: this.method,
                parameters: params,
                onSuccess: success,
                onFailure: json_failure,
            })
        };
        
        renderComponentForm(getDialog(), params, form_observe);
    });
    
    $('id_form_case_component').observe('submit', function(e) {
        e.stop();
        var parameters = {
            'a': this.serialize(true)['a'],
            'case': Nitrate.TestCases.Instance.pk,
            'o_component': this.serialize(true)['component'],
        };
        
        if(!parameters['o_component'])
            return false
        
        var c = confirm(default_messages.confirm.remove_case_component);
        if(!c)
            return false
        
        updateCaseComponent(this.action, parameters, json_success_refresh_page);
    })
    
    $$('.link_remove_component').invoke('observe', 'click', function(e) {
        var c = confirm(default_messages.confirm.remove_case_component);
        if(!c)
            return false
        
        var form = $('id_form_case_component');
        var parameters = {
            'a': form.serialize(true)['a'],
            'case': Nitrate.TestCases.Instance.pk,
            'o_component': $$('input[name="component"]')[$$('.link_remove_component').indexOf(this)].value,
        };
        updateCaseComponent(form.action, parameters, json_success_refresh_page);
    });
    
    bindSelectAllCheckbox($('id_checkbox_all_components'), $('id_form_case_component'), 'component');
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    }
    if($('id_table_cases')) {
        TableKit.Sortable.init('id_table_cases',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'
        });
    }
}

Nitrate.TestCases.Create.on_load = function()
{
    // bind_component_selector_to_product(false, false, $('id_product'), $('id_component'));
    // bind_category_selector_to_product(false, false, $('id_product'), $('id_category'));
    
    SelectFilter.init("id_component", "component", 0, "/admin_media/");
    bindRefreshComponentCategoryByProduct($('id_refresh_product'));
}

Nitrate.TestCases.Edit.on_load = function()
{
    bind_category_selector_to_product(false, false, $('id_product'), $('id_category'));
    // bind_component_selector_to_product(false, false, $('id_product'), $('id_component'));
    SelectFilter.init("id_component", "component", 0, "/admin_media/");
    // bindRefreshComponentCategoryByProduct($('id_refresh_product'));
}

Nitrate.TestCases.Clone.on_load = function()
{
    bind_version_selector_to_product(true);
    
    $('id_form_search_plan').observe('submit', function(e) {
        e.stop();
        
        var url = '/plans/';
        var container = $('id_plan_container')
        
        container.show()
        new Ajax.Updater(container, url, {
            method: 'get',
            parameters: this.serialize()
        })
    })
    
    $('id_use_filterplan').observe('click', function(e) {
        $('id_form_search_plan').enable();
        $('id_plan_id').value = '';
        $('id_plan_id').name = '';
    });
    
    $('id_use_sameplan').observe('click', function(e) {
        $('id_form_search_plan').disable();
        $('id_plan_id').value = $F('value_plan_id');
        $('id_plan_id').name = 'plan';
        $('id_plan_container').update('<div class="ajax_loading"></div>');
        $('id_plan_container').hide();
    });
}

function toggleTestCaseContents(template_type, container, content_container, object_pk, case_text_version, case_run_id, callback)
{
    if (typeof(container) != 'object')
    var container = $(container)
    
    if(typeof(content_container) != 'object')
    var content_container = $(content_container)
    
    content_container.toggle();
    
    if ($('id_loading_' + object_pk)) {
        var url = getURLParam(object_pk).url_case_details;
        var parameters = {
            template_type: template_type,
            case_text_version: case_text_version,
            case_run_id: case_run_id,
        };
        
        new Ajax.Updater(content_container, url, {
            method: 'get',
            parameters: parameters,
            onComplete: callback,
            onFailure: html_failure
        });
    };
    
    var blind_icon = container.getElementsBySelector('.blind_icon')[0]
    if (content_container.getStyle('display') == 'none') {
        $(blind_icon).removeClassName('collapse');
        $(blind_icon).addClassName('expand');
        $(blind_icon).src = "/media/images/t1.gif";
    } else {
        $(blind_icon).removeClassName('expand');
        $(blind_icon).addClassName('collapse');
        $(blind_icon).src = "/media/images/t2.gif";
    }
}

function changeTestCaseStatus(selector, case_id)
{
    var value = selector.value;
    var label = selector.previous();
    
    var success = function(t) {
        var returnobj = t.responseText.evalJSON(true); 
        var case_status_id = returnobj.case_status_id; 
        
        for (var i = 0; (node = selector.options[i]); i++) {
            if(node.selected)
            var case_status = node.innerHTML;
        }
        
        label.innerHTML = case_status;
        label.show(); 
        selector.hide();
    }
    
    changeCasesStatus(case_id, value, success);
}

function toggleAllCheckBoxes(element, container, name)
{
    if(element.checked) {
        $(container).adjacent('input[name="' + name + '"]:unchecked').each(function(e) {
            e.checked = true;
        })
    } else {
        $(container).adjacent('input[name="'+ name + '"]:checked').each(function(e) {
            e.checked = false;
        })
    }
}

function blinddownAllCases()
{
    $$('.collapse').each(function(e) {
        fireEvent(e, 'click');
    })
    
    if($('id_blind_all_link')) {
        $('id_blind_all_link').href="javascript:blindupAllCases()";
        $('id_blind_all_img').src="/media/images/t2.gif";
    }
}

function blindupAllCases()
{
    $$('.expand').each(function(e) {
        fireEvent(e, 'click');
    })
    
    if($('id_blind_all_link')) {
        $('id_blind_all_link').href="javascript:blinddownAllCases()";
        $('id_blind_all_img').src="/media/images/t1.gif";
    }
}

function changeCaseOrder(parameters, callback)
{
    nsk = prompt('Enter your new order number', parameters['sortkey'])   // New sort key
    
    if(!nsk)
    return false
    
    if(nsk != parseInt(nsk)) {
        alert('The value must be an integer number and limit between 0 to 32300.');
        return false;
    }
    
    if(nsk > 32300 || nsk < 0) {
        alert('The value must be an integer number and limit between 0 to 32300.');
        return false;
    }
    
    if(nsk == parameters['sortkey']) {
        alert('Nothing changed');
        return false;
    }
    
    var ctype = 'testcases.testcase';
    var object_pk = parameters['case'];
    var field = 'sortkey';
    var value = nsk;
    var vtype = 'int';
    
    updateObject(ctype, object_pk, field, value, vtype, callback);
}

function changeCasesStatus(object_pk, value, callback)
{
    var ctype = 'testcases.testcase';
    var field = 'case_status';
    var vtype = 'int';
    updateObject(ctype, object_pk, field, value, vtype, callback);
}

function changeCasePriority(object_pk, value, callback)
{
    var ctype = 'testcases.testcase';
    var field = 'priority';
    var vtype = 'int';
    updateObject(ctype, object_pk, field, value, vtype, callback);
}

function bind_plan_selector_to_product_version(allow_blank)
{
    $('id_version_id').observe('change', 
        getPlansByVersionId.curry(allow_blank)
    );
    getPlansByVersionId(allow_blank);
}

function getPlansByVersionId(allow_blank)
{
    if(!$F('id_version_id')) {
        return false;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        set_up_choices($('id_plan_id'), returnobj.collect(function(e) {
            return [e.pk, e.fields.name];
        }), allow_blank);
    }
        
    var failure = function(t) {
        alert("Update plan failed");
    }
    
    var url = '/plans/';
    new Ajax.Request(url, {
        method:'get',
        parameters: $('id_clone_form').serialize(true),
        requestHeaders: { Accept: 'application/json' },
        onSuccess:success, 
        onFailure:failure
    });
}

/* Using in old review, pending to remove
 *
function showCaseLog(container, case_id)
{
    $(container).show();
    var url = new String('/case/' + case_id + '/log/');
    new Ajax.Updater(container, url);
}
*/

function addCaseBug(form, callback)
{
    var complete = function(t) {
        if($('response')) {
            alert($('response').innerHTML);
            return false;
        };
        
        if(callback)
            callback();
    }
    
    new Ajax.Updater('bug', form.action, {
        method: form.method,
        parameters: $(form).serialize(true),
        onComplete: complete,
    })
}

function removeCaseBug(id, case_id, callback)
{
    if(!confirm('Are you sure to remove the bug?'))
        return false;
    
    var parameteres = {
        'handle': 'remove',
        id: id,
    }
    
    var complete = function(t) {
        if($('response')) {
            alert($('response').innerHTML);
            return false;
        }
    }
    
    new Ajax.Updater('bug', '/case/' + case_id + '/bug/', {
        method: 'get',
        parameters: parameteres,
        onComplete: complete,
    })
}

function constructPlanCaseZone(container, case_id, parameters)
{
    // $(container).update('<div class="ajax_loading"></div>');
    
    var complete = function(t) {
        $('id_plan_form').observe('submit', function(e) {
            e.stop();
            
            var callback = function(e) {
                e.stop();
                var plan_ids = this.serialize(true)['plan_id'];
                if (!plan_ids) {
                    alert('You must specific one plan at least!');
                    return false;
                }
                
                var p = {
                    a: 'add',
                    plan_id: plan_ids,
                };
                
                constructPlanCaseZone(container, case_id, p);
                clearDialog();
            }
            
            var p = this.serialize(true)
            if (!p.pk__in) {
                alert('Plan is required');
                return false;
            };
            
            previewPlan(p, getURLParam(case_id).url_case_plan, callback);
        })
    }
    var url = getURLParam(case_id).url_case_plan;
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
}

function removePlanFromCase(container, plan_id, case_id)
{
    c = confirm('Are you sure to remove the case from this plan?');
    if(!c)
    return false;
    var parameters = {
        a: 'remove',
        plan_id: plan_id,
    };
    constructPlanCaseZone(container, case_id, parameters)
}

function bindRefreshComponentCategoryByProduct(btn_refresh) {
    btn_refresh.observe('click', function(e) {
        var from = 'id_component_from';
        var to = 'id_component_to';
        var from_field = $(from);
        var to_field = $(to);
        
        to_field.update('');
        
        getComponentsByProductId(false, $('id_product'), from_field, function() {
            SelectBox.cache[from] = new Array();
            SelectBox.cache[to] = new Array();
            
            for (var i = 0; (node = from_field.options[i]); i++) {
                SelectBox.cache[from].push({value: node.value, text: node.text, displayed: 1});
            }
        });
        getCategorisByProductId(false, $('id_product'), $('id_category'));
    })
}

function taggleAllCasesCheckbox(container)
{
    if($('id_check_all_cases').checked) {
        $$('#' + container + ' input[type="checkbox"][name="case"]').each( function(t) { t.checked = true; });
        $$('#' + container + ' tr').each(function(e) { e.addClassName('selection_row')});
    } else {
        $$('#' + container + ' input[type="checkbox"][name="case"]').each( function(t) { t.checked = false; });
        $$('#' + container + ' tr').each(function(e) { e.removeClassName('selection_row')});
    }
}

function renderComponentForm(container, parameters, form_observe)
{
    var d = new Element('div');
    if(!container)
    var container = getDialog();
    container.show();
    
    var callback = function(t) {
        var action = getURLParam().url_cases_component;
        var notice = '';
        
        var h = new Element('input', {'type': 'hidden', 'name': 'a', 'value': 'add'});
        var a = new Element('input', {'type': 'submit', 'value': 'Add'});
        var r = new Element('input', {'type': 'submit', 'value': 'Remove'});
        var c = new Element('label');
        c.appendChild(h);
        c.appendChild(a);
        c.appendChild(r);
        
        a.observe('click', function(e) { h.value = 'add'});
        r.observe('click', function(e) {h.value = 'remove'});
        
        var f = constructForm(d.innerHTML, action, form_observe, notice, c);
        container.update(f);
        
        bind_component_selector_to_product(false, false, $('id_product'), $('id_o_component'));
    }
    
    var url = getURLParam().url_cases_component;
    
    new Ajax.Updater(d, url, {
        method: 'get',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    })
}

function updateCaseComponent(url, parameters, callback)
{
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    })
}

function constructCaseAutomatedForm(container, parameters, callback)
{
    if (!parameters['case']) {
        alert(default_messages.alert.no_case_selected);
        return false;
    };
    container.update(getAjaxLoading());
    container.show();
    var d = new Element('div', { 'class': 'automated_form' });
    var c = function(t) {
        var returntext = t.responseText;
        var action = '/cases/automated/';
        var form_observe = function(e) {
            e.stop();
            var params = this.serialize(true);
            params['case'] = parameters['case'];
            new Ajax.Request(getURLParam().url_cases_automated, {
                method: 'post',
                parameters: params,
                onSuccess: callback,
            });
        }
        var f = constructForm(returntext, action, form_observe);
        console.log(f);
        container.update(f);
    }
    
    getForm(d, 'testcases.CaseAutomatedForm', parameters, c);
}

function serializeCaseFromInputList(table)
{
    var elements = $(table).adjacent('input[name="case"]:checked');
    var case_ids = new Array();
    for (i in elements) {
        if (typeof(elements[i].value) == 'string')
        case_ids.push(elements[i].value);
    };
    return case_ids
}

function serialzeCaseForm(form, table, serialized)
{
    if(typeof(serialized) != 'boolean')
    var serialized = true;
    var data = form.serialize(serialized);
    data['case'] = serializeCaseFromInputList(table);
    return data
}
