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
    
    $('id_checkbox_all_case').observe('click', function(e) {
        clickedSelectAll(this, this.up(4), 'case')
    });
    
    if($('testcases_table')) {
//        SortableTable.setup({
//            rowEvenClass : 'evenRow',
//            rowOddClass : 'oddRow',
//            nosortClass : 'nosort'
//        });
//        
//        SortableTable.init('testcases_table');

        TableKit.Sortable.init('testcases_table',
        {
        	rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'
        });
    }
}

Nitrate.TestCases.Details.on_load = function()
{
    if($('id_case_id'))
        case_id = $F('id_case_id');
    else {
        alert('Can not get the case id');
        return false;
    }
    
    constructTagZone('tag', { 'case': case_id });
    
    $$('li.tab a').invoke('observe', 'click', function(i) {
        $$('div.tab_list').invoke('hide');
       $$('li.tab').invoke('removeClassName', 'tab_focus');
       this.parentNode.addClassName('tab_focus');
       $(this.title).show();
    })
    
    $('id_plan_form').observe('submit', function(e) {
        e.stop();
        $('id_preview_plan').show();
        var container = $('id_preview_plan_container');
        container.update('<div class="ajax_loading"></div>');
        previewPlan(container, this.serialize(true));
        
    })
    
    $('id_addplan_confirm').observe('click',function(e){
        if($('id_form_plan_preview')) {
            var parameters = $('id_form_plan_preview').serialize(true);
            plan_id=parameters.plan_id;
            addPlantocase(plan_id, case_id, 'plan');
        } else {
            alert('The plan is not exist in database, please type another one.');
            return false;
        }
    })
    
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
            params['a'] = 'update';
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
        }
        
        renderComponentForm(getDialog(), params, form_observe);
    });
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
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
    // bind_category_selector_to_product(false, false, $('id_product'), $('id_category'));
    // bind_component_selector_to_product(false, false, $('id_product'), $('id_component'));
    SelectFilter.init("id_component", "component", 0, "/admin_media/");
    bindRefreshComponentCategoryByProduct($('id_refresh_product'));
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


function getTestCaseParam(id){
    var param = new Object();

    param.hidenbox  = 'hidenRow_' + id;
    param.blind_icon = "blind_icon_" + id;
    param.testcase_link = "link_" + id;
    param.blind_link = "blind_link_" + id;
    param.blind_icon = "blind_icon_" + id;

    param.case_run_container = 'id_container_case_run_' + id;
    param.case_run_status_id = "id_case_run_status_icon_" + id;

    param.testcase_status_icon = "testcase_status_icon_" + id;

    param.case_status = "case_status_" + id;
    param.case_status_select = "case_status_select_" + id;

    param.case_run_status = "case_run_status_" + id;

    param.assignee = "id_link_assignee_" + id;
    param.tester = "id_link_tester_" + id;

    param.comment = "comment_" + id;
    param.notes = "case_run_notes_"  + id;

    param.case_text = 'id_case_text_' + id;
    param.tr = 'id_tr_case_' + id;
    
    return param;
}


function getTestCaseNextParam(id)
{
    var id = id + 1;

    var param = new Object();

    param.hidenbox  = 'hidenRow_' + id;
    param.blind_icon = "blind_icon_" + id;
    param.testcase_link = "link_" + id;
    param.blind_link = "blind_link_" + id;
    param.blind_icon = "blind_icon_" + id;
    param.testcase_status_icon = "testcase_status_icon_" + id;
    return param;
}


function toggleTestCaseContents(id, case_text_version, case_run_id)
{
    // FIXME: It will be replaced with CSS Selector
    var p = getTestCaseParam(id);
    
    var failure = function(t) {
        alert('Update case text failed')
    }
    
    if($(p.hidenbox) && $(p.hidenbox).getStyle('display') == 'none') {
        $(p.hidenbox).show();
        
        if($(p.blind_icon)) {
            $(p.blind_icon).removeClassName('up');
            $(p.blind_icon).addClassName('down');
        }
        
        if($(p.blind_icon))
            $(p.blind_icon).src = "/media/images/t2.gif";
        
        if($(p.case_text)) {
            url = '/case/' + $$('input[name="case"]')[id-1].value + '/details/'
            new Ajax.Updater(p.hidenbox, url, {
                method: 'get',
                parameters: {
                    case_text_version: case_text_version,
                    case_run_id: case_run_id,
                },
                onFailure: failure
            })
        }
    } else {
        $(p.hidenbox).hide();
        
        if($(p.blind_icon)) {
            $(p.blind_icon).removeClassName('down');
            $(p.blind_icon).addClassName('up');
        }
        
        if($(p.blind_icon))
            $(p.blind_icon).src = "/media/images/t1.gif";
    }
}

//function toggleTestCaseContents(id)
//{
    // FIXME: It will be replaced with CSS Selector
    //$('hidenRow_'+id).toggle();
        
//}

function changeTestCaseStatus(id, case_id)
{
    var p = getTestCaseParam(id);
    var value = $(p.case_status_select).value;
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true); 
        case_status_id = returnobj.case_status_id; 
        
        for (var i = 0; (node = $(p.case_status_select).options[i]); i++) {
           if(node.selected)
               var case_status = node.innerHTML;
        }
        
        $(p.case_status).innerHTML = case_status;
        $(p.case_status).show(); 
        $(p.case_status_select).hide();
    }
    
    changeCaseStatus(case_id, value, success);
}

function blinddownNextTestCaseContents(index_id) {
    var p = getTestCaseParam(id);
    var id = new Number(id);
    
    var next = $$('div.execute_case_run')[index_id];
    
    if(next) {
        fireEvent(next, 'click');
    } else {
        alert('It is the last case run');
        return false;
    }
}

function showStatusSelect(id)
{
    var p = getTestCaseParam(id);
    
    $(p.case_status).hide();
    $(p.case_status_select).show();
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
    $$('.up').each(function(e){
        fireEvent(e, 'click');
    })
    
    if($('id_blind_all_link')) {
        $('id_blind_all_link').href="javascript:blindupAllCases()";
        $('id_blind_all_img').src="/media/images/t2.gif";
    }
}

function blindupAllCases()
{
    $$('.down').each(function(e){
        fireEvent(e, 'click');
    })
    
    if($('id_blind_all_link')) {
        $('id_blind_all_link').href="javascript:blinddownAllCases()";
        $('id_blind_all_img').src="/media/images/t1.gif";
    }
}

function changeCaseOrder(case_id, sort_key, plan_id)
{
    nsk = prompt('Enter your new order number', sort_key)   // New sort key
    
    if(!nsk)
        return false
    
    if(isNaN(nsk)) {
        alert('The value must be a integer number and limit between 0 to 32300.');
        return false;
    }
    
    if(nsk > 32300 || nsk < 0) {
        alert('The value must be a integer number and limit between 0 to 32300.');
        return false;
    }
    
    if(nsk == sort_key) {
        alert('Nothing changed');
        return false;
    }
    
    // Succeed callback
    var s_callback = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        if (returnobj.rc == 0) {
            if(plan_id) {
                constructPlanDetailsCasesZone(
                    'testcases', plan_id, $('id_form_cases').serialize(true)
                );
            } else {
                window.location.reload();
            }
        } else {
            alert(returnobj.response);
        }
    }
    
    var ctype = 'testcases.testcase';
    var object_pk = case_id;
    var field = 'sortkey';
    var value = nsk;
    
    updateObject(ctype, object_pk, field, value, s_callback);
}

function changeCaseStatus(object_pk, value, callback)
{
    var ctype = 'testcases.testcase';
    var field = 'case_status';
    
    updateObject(ctype, object_pk, field, value, callback);
}

function changeCasePriority(object_pk, value, callback)
{
    var ctype = 'testcases.testcase';
    var field = 'priority';
    
    updateObject(ctype, object_pk, field, value, callback);
}

function bind_plan_selector_to_product_version(allow_blank)
{
    $('id_version_id').observe('change', 
                               getPlansByVersionId.curry(allow_blank));
    getPlansByVersionId(allow_blank);
}

function getPlansByVersionId(allow_blank)
{
    if(!$F('id_version_id')) {
        return false;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        set_up_choices(
            $('id_plan_id'), 
            returnobj.collect(function(e) {
                return [e.pk, e.fields.name];
            }),
            allow_blank
        );
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

function showCaseLog(container, case_id)
{
    $(container).show();
    var url = new String('/case/' + case_id + '/log/');
    new Ajax.Updater(container, url);
}

function addCaseBug(form)
{
    var complete = function(t) {
        if($('response')) {
            alert($('response').innerHTML);
            return false;
        }
    }
    
    new Ajax.Updater('bug', form.action, {
        method: form.method,
        parameters: $(form).serialize(true),
        onComplete: complete,
    })
}

function removeCaseBug(id)
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

function constructAddPlan(container, case_id, parameters)
{
    // $(container).update('<div class="ajax_loading"></div>');
    
    var complete = function(t) {
        $('id_addplan_confirm').observe('click',function(e){
            if($('id_form_plan_preview')) {
                var parameters = $('id_form_plan_preview').serialize(true);
                plan_id=parameters.plan_id;
                addPlantocase(plan_id, case_id, 'plan');
            } else {
                alert('The plan is not exist in database, please type another one.');
                return false;
            }
        })
        
        $('id_plan_form').observe('submit', function(e) {
            e.stop();
            $('id_preview_plan').show();
            var container = $('id_preview_plan_container');
            container.update('<div class="ajax_loading"></div>');
            previewPlan(container, this.serialize(true));
        })
        
        if($('message')) {
            alert($('message').innerHTML);
            return false;
        }
    }
    var url = new String('/case/' + case_id + '/plan/');
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
}

function addPlantocase(plan_id, case_id, container)
{
    var parameters = {
        handle: 'add',
        plan_id: plan_id,
    };
    constructAddPlan(container, case_id, parameters)
}

function removePlantocase(plan_id, case_id, container)
{
    c = confirm('Are you sure to remove the case from this plan?');
    if(!c)
        return false;
    var parameters = {
        handle: 'remove',
        plan_id: plan_id,
    };
    constructAddPlan(container, case_id, parameters)
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
        
        var f = constructForm(d.innerHTML, action, form_observe, notice);
        container.update(f);
    }
    
    var url = getURLParam().url_cases_component;
    
    new Ajax.Updater(d, url, {
        method: 'post',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    })
}
