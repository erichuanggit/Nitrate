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
    
    $('id_blind_all_link').observe('click', function(e) {
        //FIXME
        //Adding a lock here to avoid generating too much requests.
        //The lock won't be released until after all requests generated by 'expand all' are finished.
        //Unfortunately we're using $$('div[id^="id_loading_"]').length == 0.
        //Not elegant enough.
        //See https://bugzilla.redhat.com/show_bug.cgi?id=676590
        if ($$('div[id^="id_loading_"]').length == 0){
            this.removeClassName('locked');
        }
        if (this.hasClassName('locked')){
            //To disable the 'expand all' until all case runs are expanded.
            return false;
        }
        else{
            this.addClassName('locked');
            var element = this.down();
            if (element.hasClassName('collapse-all')) {
                this.title = "Collapse all cases"
                blinddownAllCases(element);
            } 
            else {
                this.title = "Expand all cases"
                blindupAllCases(element);
            };
        }
    })
    
    if(window.location.hash == '#expandall'){
        blinddownAllCases();
    }

    var oTable;
    oTable = jQ('#testcases_table').dataTable({
        "iDisplayLength": 20,
        "sPaginationType": "full_numbers",
        "bFilter": false,
        "bLengthChange": false,
        "aaSorting": [[ 2, "desc" ]],
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": "/cases/ajax/"+this.window.location.search,
        "aoColumns": [
          {"bSortable": false,"sClass": "expandable" },
          {"bSortable": false },
          {"sType": "html","sClass": "expandable"},
          {"sType": "html","sClass": "expandable"},
          {"sType": "html","sClass": "expandable"},
          {"sClass": "expandable"},
          {"sClass": "expandable"},
          {"sClass": "expandable"},
          {"sClass": "expandable"},
          {"sClass": "expandable"},
          {"sClass": "expandable"},
        ]
    });
    jQ("#testcases_table tbody tr td.expandable").live("click", function() {
        var tr = this.up();
        var case_id = tr.getElementsBySelector('input[name="case"]')[0].value;
        var detail_td = '<tr class="case_content hide" style="display: none;"><td colspan="11"><div id="id_loading_' + case_id + '" class="ajax_loading"></div></td></tr>'
        var blind_icon = tr.getElementsBySelector('.blind_icon')[0]
        if ( oTable.fnIsOpen(tr) ) {
            $(blind_icon).removeClassName('collapse');
            $(blind_icon).addClassName('expand');
            $(blind_icon).src = "/media/images/t1.gif";
            oTable.fnClose( tr );
        } else {
          oTable.fnOpen( tr, detail_td, "info_row" );
          toggleTestCaseContents("case", tr, tr.next(), case_id);
        }
    });
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
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    };
    
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
        renderCategoryForm(getDialog(), garams, form_observe);
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

    var toggle_case_run = function(e) {
        var c = this.up(); // Container
        var c_container = c.next(); // Content Containers
        var case_id = c.getElementsBySelector('input[name="case"]')[0].value;
        var case_run_id = c.getElementsBySelector('input[name="case_run"]')[0].value;
        var case_text_version = c.getElementsBySelector('input[name="case_text_version"]')[0].value;
        var type = 'case_case_run';
        toggleTestCaseContents(type, c, c_container, case_id, case_text_version, case_run_id);
    }
    
    $$('.expandable').invoke('observe', 'click', toggle_case_run);

    jQ('#testplans_table').dataTable({
        "bFilter": false,
        "bLengthChange": false,
        "bPaginate": false,
        "bInfo": false,
        "aaSorting": [[ 0, "desc" ]],
        "aoColumns": [
          null,
          null,
          {"sType": "html"},
          {"sType": "html"},
          {"sType": "html"},
          null,
          {"bSortable": false},
        ]
    });
}

/*
 * Resize all editors within the webpage after they are rendered.
 * This is used to avoid a bug of TinyMCE in Firefox 11.
 */
function resize_tinymce_editors()
{
    jQ('.mceEditor .mceIframeContainer iframe').each(
	function(item) {
	    var elem = jQ(this);
	    elem.height(elem.height() + 1);
	});
}

Nitrate.TestCases.Create.on_load = function()
{
    // bind_component_selector_to_product(false, false, $('id_product'), $('id_component'));
    // bind_category_selector_to_product(false, false, $('id_product'), $('id_category'));
    
    SelectFilter.init("id_component", "component", 0, "/admin_media/");
    //init category and components
    getCategorisByProductId(false, $('id_product'), $('id_category'));
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
    // bind change on product to update component and category
    jQ('#id_product').change(function () {
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
    });
    resize_tinymce_editors();
}

Nitrate.TestCases.Edit.on_load = function()
{
    bind_category_selector_to_product(false, false, $('id_product'), $('id_category'));
    // bind_component_selector_to_product(false, false, $('id_product'), $('id_component'));
    //SelectFilter.init("id_component", "component", 0, "/admin_media/");

    resize_tinymce_editors();
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
        $('id_copy_case').checked = true;
    });
    
    if($('id_use_sameplan')){
    $('id_use_sameplan').observe('click', function(e) {
        $('id_form_search_plan').disable();
        $('id_plan_id').value = $F('value_plan_id');
        $('id_plan_id').name = 'plan';
        $('id_plan_container').update('<div class="ajax_loading"></div>');
        $('id_plan_container').hide();
        $('id_copy_case').checked = false;
    })
    };
}

function toggleTestCaseContents(template_type, container, content_container, object_pk, case_text_version, case_run_id, callback)
{
    if (typeof(container) != 'object')
    var container = $(container)
    
    if(typeof(content_container) != 'object')
    var content_container = $(content_container)
    
    // content_container.toggle();
    
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

function changeTestCaseStatus(selector, case_id, be_confirmed, was_confirmed)
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

        if(be_confirmed){
            jQ('#run_case_count').text(parseInt(jQ('#run_case_count').text())+1);
            jQ('#review_case_count').text(parseInt(jQ('#review_case_count').text())-1);
            jQ('#'+case_id).remove();
        }
        if(was_confirmed){
            jQ('#run_case_count').text(parseInt(jQ('#run_case_count').text())-1);
            jQ('#review_case_count').text(parseInt(jQ('#review_case_count').text())+1);
            jQ('#'+case_id).remove();
        }
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

function toggleAllCases(element){
    element = $(element);
    //If and only if both case length is 0, remove the lock.
    if ($$('div[id^="id_loading_"].normal_cases').length == 0 && $$('div[id^="id_loading_"].review_cases').length == 0){
        element.removeClassName('locked');
    }

    if (element.hasClassName('locked')){
        return false;
    }
    else{
        element.addClassName('locked');
//        var element = this.down();
        if (element.hasClassName('collapse-all')) {
            element.title = "Collapse all cases"
            blinddownAllCases(element);
        } 
        else {
            element.title = "Expand all cases"
            blindupAllCases(element);
        };
        
    }
}

function blinddownAllCases(element)
{
    $$('img.expand').each(function(e) {
        fireEvent(e, 'click');
    })
    if (element) {
        element.removeClassName('collapse-all');
        element.addClassName('expand-all');
//        element.href="javascript:blindupAllCases()";
        element.src="/media/images/t2.gif";
    }
}

function blindupAllCases(element)
{
    $$('.collapse').each(function(e) {
        fireEvent(e, 'click');
    })
    
    if(element) {
        element.removeClassName('expand-all');
        element.addClassName('collapse-all');
//        element.href="javascript:blinddownAllCases()";
        element.src="/media/images/t1.gif";
    }
}
function changeCaseOrder(parameters, callback)
{
    if(parameters.hasOwnProperty('sortkey') == true){
        nsk = prompt('Enter your new order number', parameters['sortkey']);   // New sort key
        if(nsk == parameters['sortkey']) {
            alert('Nothing changed');
            return false;
        }
    }
    else
        nsk = prompt('Enter your new order number');

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
    var ctype = 'testcases.testcaseplan';
    var object_pk = parameters['testcaseplan'];
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

    //Error handling. alert if user input an invalid number.
    bug_id = form.bug_id.getValue();

    if(isNaN(bug_id) || bug_id == ""){
        alert(default_messages.alert.invalid_bug_id);
        return false;
    }

    var complete = function(t) {
        if($('response')) {
            alert($('response').innerHTML);
            return false;
        };

        if(callback)
            callback();
        jQ('#case_bug_count').text(jQ('table#bugs').attr('count'));
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
        jQ('#case_bug_count').text(jQ('table#bugs').attr('count'));
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
                jQ('#plan_count').text(jQ('table#testplans_table').attr('count'));
            }

            var p = this.serialize(true)
            if (!p.pk__in) {
                alert('Plan is required');
                return false;
            };

            previewPlan(p, getURLParam(case_id).url_case_plan, callback);
        })
        jQ('#testplans_table').dataTable({
            "bFilter": false,
            "bLengthChange": false,
            "bPaginate": false,
            "bInfo": false,
            "aaSorting": [[ 0, "desc" ]],
            "aoColumns": [
              null,
              null,
              {"sType": "html"},
              {"sType": "html"},
              {"sType": "html"},
              null,
              {"bSortable": false},
            ]
        });
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
    constructPlanCaseZone(container, case_id, parameters);
    jQ('#plan_count').text(jQ('table#testplans_table').attr('count'));
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
        var notice = 'Press "Ctrl" to select multiple default component';

        var h = new Element('input', {'type': 'hidden', 'name': 'a', 'value': 'add'});
        var a = new Element('input', {'type': 'submit', 'value': 'Add'});
        //var r = new Element('input', {'type': 'submit', 'value': 'Remove'});
        var c = new Element('label');
        c.appendChild(h);
        c.appendChild(a);
        //c.appendChild(r);

        a.observe('click', function(e) { h.value = 'add'});
        //r.observe('click', function(e) {h.value = 'remove'});

        var f = constructForm(d.innerHTML, action, form_observe, notice, c);
        container.update(f);

        bind_component_selector_to_product(false, false, $('id_product'), $('id_o_component'));
    }

    var url = getURLParam().url_cases_component;

    new Ajax.Updater(d, url, {
        method: 'post',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    })
}


function renderCategoryForm(container, parameters, form_observe)
{
    var d = new Element('div');
    if(!container)
    var container = getDialog();
    container.show();

    var callback = function(t) {
        var action = getURLParam().url_cases_category;
        var notice = 'Select Category';

        var h = new Element('input', {'type': 'hidden', 'name': 'a', 'value': 'add'});
        var a = new Element('input', {'type': 'submit', 'value': 'Select'});
        //var r = new Element('input', {'type': 'submit', 'value': 'Remove'});
        var c = new Element('label');
        c.appendChild(h);
        c.appendChild(a);
        //c.appendChild(r);

        a.observe('click', function(e) { h.value = 'update'});
        //r.observe('click', function(e) {h.value = 'remove'});

        var f = constructForm(d.innerHTML, action, form_observe, notice, c);
        container.update(f);

        bind_category_selector_to_product(false, false, $('id_product'), $('id_o_category'));
    }

    var url = getURLParam().url_cases_category;

    new Ajax.Updater(d, url, {
        method: 'post',
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

function updateCaseCategory(url, parameters, callback)
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
            if(this.getElementsBySelector('input[type="checkbox"]:checked').length == 0) {
                alert('Nothing selected');
                return false;
            }

            var params = this.serialize(true);
            params['case'] = parameters['case'];
            new Ajax.Request(getURLParam().url_cases_automated, {
                method: 'post',
                parameters: params,
                onSuccess: callback,
            });
        }
        var f = constructForm(returntext, action, form_observe);
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
function serializeSortFromInputList(table)
{
    var elements = $(table).adjacent('input[name="case"]:checked');
    var case_plan_ids = new Array();
    for(var i=0; i<elements.length; i++){
        var case_plan_element = elements[i].up(0).siblings()[10].adjacent('span')[0];
        if (typeof(case_plan_element.innerHTML) == 'string')
        case_plan_ids.push(case_plan_element.innerHTML);
    };
    return case_plan_ids
}

function serialzeCaseForm(form, table, serialized)
{
    if(typeof(serialized) != 'boolean')
    var serialized = true;
    var data = form.serialize(serialized);
    data['case'] = serializeCaseFromInputList(table);
    return data
}

function toggleDiv(link, divId){
    var link = jQ(link);
    var div = jQ('#'+divId);
    var show = 'Show All';
    var hide = 'Hide All';
    div.toggle();
    var text = link.html();
    if(text!=show){
        link.html(show);
    }else{
        link.html(hide);
    }
}
