Nitrate.TestCases = {};
Nitrate.TestCases.List = {};
Nitrate.TestCases.AdvanceList = {};
Nitrate.TestCases.Details = {};
Nitrate.TestCases.Create = {};
Nitrate.TestCases.Edit = {};
Nitrate.TestCases.Clone = {};

(function() {
    'use restrict';

    var TestCases = window.Nitrate.TestCases || {};

    TestCases.CasesSelection = function(options) {
        this.selectedCasesIds = options.selectedCasesIds || [];
        this.selectAll = options.selectAll;

        if (Object.prototype.toString.call(this.selectedCasesIds) !== '[object Array]') {
            throw new TypeError('selectedCasesIds must an object of Array.');
        }
        if (typeof this.selectAll !== 'boolean') {
            throw new TypeError('selectAll must be a boolean value.');
        }
    };

    TestCases.CasesSelection.prototype.empty = function() {
        return this.selectedCasesIds.length === 0 && !this.selectAll;
    };

    window.Nitrate.TestCases = TestCases;
}());

Nitrate.TestCases.AdvanceList.on_load = function()
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

    var toggle_case = function(e) {
        var c = this.up(); // Container
        var c_container = c.next(); // Content Containers
        var case_id = c.getElementsBySelector('input[name="case"]')[0].value;

        toggleTestCasePane({
            case_id: case_id,
            casePaneContainer: jQ(c_container)
        });
        toggleExpandArrow({
            caseRowContainer: jQ(c),
            expandPaneContainer: jQ(c_container)
        });
    }

    $$('.expandable').invoke('observe', 'click', toggle_case);


    if(window.location.hash == '#expandall'){
        blinddownAllCases();
    }

}

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
        var caseRowContainer = jQ(tr);
        var case_id = caseRowContainer.find('input[name="case"]').attr('value');

        var detail_td = '<tr class="case_content hide" style="display: none;"><td colspan="11">' +
                        '<div id="id_loading_' + case_id + '" class="ajax_loading"></div></td></tr>';
        if (!caseRowContainer.next().hasClass('hide')) {
            caseRowContainer.after(detail_td);
        }

        toggleTestCasePane({
            case_id: case_id,
            casePaneContainer: jQ(tr.next())
        });
        toggleExpandArrow({
            caseRowContainer: jQ(tr),
            expandPaneContainer: jQ(tr.next())
        });
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

            var url = Nitrate.http.URLConf.reverse({
                name: 'cases_component'
            });
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
        // FIXME: case_text_version is not used in the backend to show caserun
        // information, notes, logs, and comments.
        var case_text_version = c.getElementsBySelector('input[name="case_text_version"]')[0].value;
        var type = 'case_case_run';
        toggleSimpleCaseRunPane({
            caserunRowContainer: jQ(c),
            expandPaneContainer: jQ(c_container),
            caseId: case_id,
            caserunId: case_run_id
        });
    }

    var toggle_case_runs_by_plan = function(e) {
        var c = this.up();
        var case_id = c.getElementsByTagName('input')[0].value;
        var params = {
            'type' : 'case_run_list',
            'container': c,
            'c_container': c.next(),
            'case_id': case_id,
            'case_run_plan_id': c.id
        }
        var callback = function(e) {
            $$('#table_case_runs_by_plan .expandable').invoke('observe', 'click', toggle_case_run);
        }
        toggleCaseRunsByPlan(params, callback);
    }
    $$('.plan_expandable').invoke('observe', 'click', toggle_case_runs_by_plan);
    jQ('#testplans_table').dataTable({
        "bFilter": false,
        "bLengthChange": false,
        "bPaginate": false,
        "bInfo": false,
        "bAutoWidth": false,
        "aaSorting": [[ 0, "desc" ]],
        "aoColumns": [
          {"sType": "num-html"},
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

    SelectFilter.init("id_component", "component", 0, "/static/admin/");
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
    //SelectFilter.init("id_component", "component", 0, "/static/admin/");

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


/*
 * Used for expanding test case in test plan page specifically
 *
 * Arguments:
 * options.caseRowContainer: a jQuery object referring to the container of the
 *                           test case that is being expanded to show more
 *                           information.
 * options.expandPaneContainer: a jQuery object referring to the container of
 *                              the expanded pane showing test case detail
 *                              information.
 */
function toggleExpandArrow(options) {
    var container = options.caseRowContainer;
    var content_container = options.expandPaneContainer;

    var blind_icon = container.find('img.blind_icon');
    if (content_container.css('display') == 'none') {
        blind_icon.removeClass('collapse');
        blind_icon.addClass('expand');
        blind_icon.attr('src', '/static/images/t1.gif');
    } else {
        blind_icon.removeClass('expand');
        blind_icon.addClass('collapse');
        blind_icon.attr('src', '/static/images/t2.gif');
    }
}


/*
 * Toggle simple caserun pane in Case Runs tab in case page.
 */
function toggleSimpleCaseRunPane(options) {
    var container = options.caserunRowContainer;
    var content_container = options.expandPaneContainer;
    var caseId = options.caseId;
    var caserunId = options.caserunId;

    content_container.toggle();

    if (container.next().find('.ajax_loading').length !== 0) {
        var url = '/case/' + caseId + '/caserun-simple-pane/';
        var data = {case_run_id: caserunId};

        jQ.get(url, data, function(data, textStatus) {
            content_container.html(data);
        },
        'html');
    }

    toggleExpandArrow({
        caseRowContainer: container,
        expandPaneContainer: content_container
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
        var url = Nitrate.http.URLConf.reverse({
            name: 'case_details',
            arguments: {id: object_pk}
        });
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

    toggleExpandArrow({
        caseRowContainer: jQ(container),
        expandPaneContainer: jQ(content_container)
    });
}

function changeTestCaseStatus(plan_id, selector, case_id, be_confirmed, was_confirmed)
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

        // container should be got before selector is hidden.
        var curCasesContainer = jQ(selector).parents('.tab_list');

        label.innerHTML = case_status;
        label.show();
        selector.hide();

        if( be_confirmed || was_confirmed){
            jQ('#run_case_count').text(returnobj.run_case_count);
            jQ('#case_count').text(returnobj.case_count);
            jQ('#review_case_count').text(returnobj.review_case_count);
            jQ('#'+case_id).next().remove();
            jQ('#'+case_id).remove();

            // We have to reload the other side of cases to reflect the status
            // change. This MUST be done before selector is hided.
            Nitrate.TestPlans.Details.reopenTabHelper(curCasesContainer);
        }
    }

    changeCasesStatus(plan_id, case_id, value, success);
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
        element.src="/static/images/t2.gif";
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
        element.src="/static/images/t1.gif";
    }
}

// Deprecated. Remove when it's unusable any more.
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

function changeCaseOrder2(parameters, callback) {
    if (parameters.hasOwnProperty('sortkey') == true) {
        nsk = prompt('Enter your new order number', parameters['sortkey']);   // New sort key
        if(nsk == parameters['sortkey']) {
            alert('Nothing changed');
            return false;
        }
    }
    else {
        nsk = prompt('Enter your new order number');
    }

    if(!nsk) {
        return false;
    }

    if(nsk != parseInt(nsk)) {
        alert('The value must be an integer number and limit between 0 to 32300.');
        return false;
    }

    if(nsk > 32300 || nsk < 0) {
        alert('The value must be an integer number and limit between 0 to 32300.');
        return false;
    }

    parameters.target_field = 'sortkey';
    parameters.new_value = nsk;

    new Ajax.Request('/ajax/update/cases-sortkey/', {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    });
}

// Deprecated. dead code.
function changeCasesStatus(plan_id, object_pk, value, callback)
{
    var plan_id = plan_id;
    var ctype = 'testcases.testcase';
    var field = 'case_status';
    var vtype = 'int';
    updateCaseStatus(plan_id, ctype, object_pk, field, value, vtype, callback);
}

// Deprecated. dead code.
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
                    alert(default_messages.alert.no_plan_specified);
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
                alert(default_messages.alert.no_plan_specified);
                return false;
            };

            var url = Nitrate.http.URLConf.reverse({
                name: 'case_plan',
                arguments: {id: case_id}
            });
            previewPlan(p, url, callback);
        });
        if (jQ('#testplans_table td a').length > 0) {
            jQ('#testplans_table').dataTable({
                "bFilter": false,
                "bLengthChange": false,
                "bPaginate": false,
                "bInfo": false,
                "bAutoWidth": false,
                "aaSorting": [[ 0, "desc" ]],
                "aoColumns": [
                  {"sType": "num-html"},
                  null,
                  {"sType": "html"},
                  {"sType": "html"},
                  {"sType": "html"},
                  null,
                  {"bSortable": false},
                ]
            });
        }
    }

    var url = Nitrate.http.URLConf.reverse({
        name: 'case_plan',
        arguments: {id: case_id}
    });

    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    });
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

function renderTagForm(container, parameters, form_observe)
{
    var d = new Element('div');
    if(!container)
    var container = getDialog();
    container.show();

    var callback = function(t) {
        var action = Nitrate.http.URLConf.reverse({
            name: 'cases_tag'
        });
        var notice = 'Press "Ctrl" to select multiple default component';

        var h = new Element('input', {'type': 'hidden', 'name': 'a', 'value': 'remove'});
        var a = new Element('input', {'type': 'submit', 'value': 'Remove'});
        var c = new Element('label');
        c.appendChild(h);
        c.appendChild(a);
        a.observe('click', function(e) { h.value = 'remove'});
        var f = constructForm(d.innerHTML, action, form_observe, notice, c);
        container.update(f);
        bind_component_selector_to_product(false, false, $('id_product'), $('id_o_component'));
    };
    var url = Nitrate.http.URLConf.reverse({
        name: 'cases_tag'
    });
    new Ajax.Updater(d, url, {
        method: 'post',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    });
}


function renderComponentForm(container, parameters, form_observe)
{
    var d = new Element('div');
    if(!container)
    var container = getDialog();
    container.show();

    var callback = function(t) {
        var action = Nitrate.http.URLConf.reverse({
            name: 'cases_component'
        });
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

    var url = Nitrate.http.URLConf.reverse({
        name: 'cases_component'
    });

    new Ajax.Updater(d, url, {
        method: 'post',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    });
}


function renderCategoryForm(container, parameters, form_observe)
{
    var d = new Element('div');
    if(!container)
    var container = getDialog();
    container.show();

    var callback = function(t) {
        var action = Nitrate.http.URLConf.reverse({
            name: 'cases_category'
        });
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

    var url = Nitrate.http.URLConf.reverse({
        name: 'cases_category'
    });

    new Ajax.Updater(d, url, {
        method: 'post',
        parameters: parameters,
        onComplete: callback,
        onFailure: html_failure,
    });
}

// FIXME: abstract this function
function updateCaseTag(url, parameters, callback)
{
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    })
}

// FIXME: this
function updateCaseComponent(url, parameters, callback)
{
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    })
}

// FIXME: this, and other code that calls Ajax.Request
function updateCaseCategory(url, parameters, callback)
{
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    })
}

function constructCaseAutomatedForm(container, callback, options)
{
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

            var params = serializeFormData({
                form: this,
                zoneContainer: options.zoneContainer,
                casesSelection: options.casesSelection
            });
            /*
             * Have to add this. The form generated before does not contain a
             * default value `change'. In fact, the field a onust contain the
             * only value `change', here.
             */
            params = params.replace(/a=\w*/, 'a=change');
            var url = Nitrate.http.URLConf.reverse({
                name: 'cases_automated'
            });
            new Ajax.Request(url, {
                method: 'post',
                parameters: params,
                onSuccess: callback,
            });
        }
        var f = constructForm(returntext, action, form_observe);
        container.update(f);
    }

    getForm(d, 'testcases.CaseAutomatedForm', {}, c);
}

/*
 * Serialize selected cases' Ids.
 *
 * This function inherits the ability from original definition named
 * serializeCaseFromInputList, except that it also collects whehter all cases
 * are also selected even through not all of cases are displayed.
 *
 * Return value is an object of dictionary holding two properties. `selectAll'
 * is a boolean value indicating whether user select all cases.
 * `selectedCasesIds' is an array containing all selected cases' Ids the
 * current loaded set of cases.
 *
 * Whatever user selects all cases, above two properties appears always with
 * proper value.
 */
function serializeCaseFromInputList2(table) {
    var selectAll = jQ(table).parent()
                                .find('.js-cases-select-all')
                                .find('input[type="checkbox"]')
                                .attr('checked');

    var case_ids = [];
    var checkedCases = jQ(table).find('input[name="case"]:checked');
    checkedCases.each(function(i, checkedCase) {
        if (typeof(checkedCase.value) === 'string') {
            case_ids.push(checkedCase.value);
        }
    });
    var selectedCasesIds = case_ids;

    return new Nitrate.TestCases.CasesSelection({
        selectedCasesIds: selectedCasesIds,
        selectAll: selectAll
    });
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
function serializeCasePlanIDFromInputList(table)
{
    var elements = $(table).adjacent('input[name="case"]:checked');
    var case_plan_ids = new Array();
    for(var i=0; i<elements.length; i++){
        var tr_element = elements[i].up(1);
        var case_plan_element = tr_element.getElementsByClassName('col_sortkey_content')[0].getElementsByTagName('span')[0];
        if (typeof(case_plan_element.innerHTML) == 'string')
        case_plan_ids.push(case_plan_element.innerHTML);
    };
    return case_plan_ids
}

/*
 * Serialize criterias for searching cases.
 *
 * Arguments:
 * - form: the form from which criterias are searched
 * - table: the table containing all loaded cases
 * - serialized: whether to serialize the form data. true is default, if not
 *   passed.
 * - exclude_cases: whether to exclude all cases while serializing. For
 *   instance, when filter cases, it's unnecessary to collect all selected
 *   cases' IDs, due to all filtered cases in the response should be selected
 *   by default. Default to true if not passed.
 */
function serialzeCaseForm(form, table, serialized, exclude_cases)
{
    if(typeof(serialized) != 'boolean')
    var serialized = true;
    if (exclude_cases === undefined) {
        exclude_cases = false;
    }
    var data = form.serialize(serialized);
    if (!exclude_cases) {
        data['case'] = serializeCaseFromInputList(table);
    }
    return data
}

/*
 * New implementation of serialzeCaseForm to allow to choose whether the
 * TestCases' Ids are necessary to be serialized.
 *
 * Be default if no value is passed to exclude_cases, not exclude them.
 */
function serializeCaseForm2(form, table, serialized, exclude_cases)
{
    if(typeof(serialized) != 'boolean')
    var serialized = true;
    var data = form.serialize(serialized);
    var _exclude = exclude_cases === undefined ? false : exclude_cases;
    if (!_exclude) {
        data['case'] = serializeCaseFromInputList(table);
    }
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

function addCaseBugViaEnterKey(element, e){
    if (e.keyCode == 13)
        addCaseBug(element);
}

function toggleCaseRunsByPlan(params, callback)
{
    var container = params.container;
    var content_container = params.c_container;
    var case_run_plan_id = params.case_run_plan_id;
    var case_id = params.case_id;
    if (typeof(container) != 'object')
        container = $(container);

    if(typeof(content_container) != 'object')
        content_container = $(content_container);

    content_container.toggle();

    if ($('id_loading_' + case_run_plan_id)) {
        var url = '/case/' + case_id + '/caserun-list-pane/';
        var parameters = {
            plan_id: case_run_plan_id
        };

        new Ajax.Updater(content_container, url, {
            method: 'get',
            parameters: parameters,
            onComplete: callback,
            onFailure: html_failure
        });
    };

    var blind_icon = container.getElementsByTagName('img')[0];
    if (content_container.getStyle('display') == 'none') {
        $(blind_icon).removeClassName('collapse');
        $(blind_icon).addClassName('expand');
        $(blind_icon).src = "/static/images/t1.gif";
    } else {
        $(blind_icon).removeClassName('expand');
        $(blind_icon).addClassName('collapse');
        $(blind_icon).src = "/static/images/t2.gif";
    }
}
