Nitrate.TestRuns = {};
Nitrate.TestRuns.List = {};
Nitrate.TestRuns.Details = {};
Nitrate.TestRuns.New = {};
Nitrate.TestRuns.Edit = {};
Nitrate.TestRuns.Execute = {}
Nitrate.TestRuns.Clone = {};
Nitrate.TestRuns.AssignCase = {}

Nitrate.TestRuns.List.on_load = function()
{
    bind_version_selector_to_product(true, $('id_product'));
    bind_build_selector_to_product(true, $('id_product'));
    
    if($('testruns_table')) {
        SortableTable.setup({
            rowEvenClass : 'evenRow',
            rowOddClass : 'oddRow',
            nosortClass : 'nosort'
        });

        SortableTable.init('testruns_table');
    }

    $('id_search_people').name = $F('id_people_type');
    
    $('id_people_type').observe('change', function() {
        $('id_search_people').name = $F('id_people_type');
    })

    $('run_column_add').observe('change', function(t) {
        switch(this.value) {
            case 'col_plan':
                $('col_plan_head').show();
                $$('.col_plan_content').each(function(t){ t.show() });
                $('col_plan_option').hide();
                break;
        }
        
    })


}

Nitrate.TestRuns.Details.on_load = function()
{
    if($('id_sort'))
        $('id_sort').observe('click', taggleSortCaseRun);
    
    $('id_check_all_button').observe('click', function(m) {
        toggleAllCheckBoxes(this, 'id_table_cases', 'case_run');
    })
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    }
}

Nitrate.TestRuns.New.on_load = function()
{
    if($('testcases')) {
        SortableTable.setup({
            nosortClass : 'nosort'
        });

        SortableTable.init('testcases');
    }
    if($('testcases_filter')) {
        SortableTable.setup({
            rowEvenClass : 'even',
            rowOddClass : 'odd',
            nosortClass : 'nosort'
        });

        SortableTable.init('testcases_filter');
    }

}

Nitrate.TestRuns.Edit.on_load = function()
{
    bind_version_selector_to_product(false);
    bind_build_selector_to_product(false);
}

Nitrate.TestRuns.Execute.on_load = function()
{
    // Bind the display
    bindExecuteShowCommment('executeList');
    bindExecuteCommentForm('executeList');
    
    if(window.location.hash) {
        blindupAllCases();
        
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    }
    $('id_check_box_blinddownallcase').observe('click',function(){
        if($('id_check_box_blinddownallcase').checked){
            blinddownAllCases();
        } else {
            blindupAllCases();
        }
    })
	if($('id_check_box_highlight').checked){
		$$('.mine').invoke('addClassName','highlight');
		}
	$('id_check_box_highlight').observe('click',function(){
		e=$$('.mine');
		this.checked && e.invoke('addClassName','highlight') || e.invoke('removeClassName','highlight')
		})
}

Nitrate.TestRuns.Clone.on_load = function()
{
    bind_version_selector_to_product(false);
    bind_build_selector_to_product(false);
}

Nitrate.TestRuns.AssignCase.on_load= function()
{
    if($('id_check_all_button')) {
        $('id_check_all_button').observe('click', function(m) {
            toggleAllCheckBoxes(this, 'id_table_cases', 'case')
        })
    }
    
    $$('input[name="case"]').invoke('observe', 'click', function(t) {
        if(this.checked) {
            this.up(1).addClassName('selection_row');
            this.up().next(8).update('<div class="apply_icon"></div>');
        } else {
            this.up(1).removeClassName('selection_row');
            this.up().next(8).update('');
        }
    })
}

function bindExecuteShowCommment(container, parameters)
{
    $(container).adjacent('a.link_show_comments').invoke('observe', 'click', function(e) {
        var container = this.up(1).next();
        
        container.toggle();
        constructCommentZone(container, this.parentNode.serialize(true));
        
        if(container.getStyle('display') == 'none')
            this.update('Show comments');
        else
            this.update('Hide comments');
    })
}

/*
// Rewrite with observe in bindCommentDeleteLink() of tcms_actions.js

function commentdelete(comment_id){
    if(!confirm('Are you sure to delete the comment?'))
        return false;
    
    var delete_link = this;
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        if (returnobj.rc == 0) {
            var container = delete_link.up(2);
            var parameters = delete_link.up(2).previous().down().serialize(true);
            constructCommentZone(container, parameters);
        } else {
            alert(returnobj.response);
        }
    }
    var failure = function(t) {
        alert("Delete comment failed");
    }
    var url = '/comments/delete/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'comment_id': comment_id,
        },
        onSuccess: success, 
        onFailure: failure,
    });
}
*/

function unbindExecuteShowCommment(container)
{
    $(container).adjacent('a.link_show_comments').invoke('stopObserving', 'click');
}

function unbindCaseRunStatusForm(object)
{
    $$(object).invoke('stopObserving')
}

function bindCaseRunStatusForm(object)
{
    $$(object).invoke('observe', 'submit', function(e) {
        e.stop();
        changeCaseRunStatus(this);
    })
}

function bindExecuteCommentForm(container)
{
    $(container).adjacent('form.comment_form').invoke('observe', 'submit', function(e) {
        e.stop();
        
        var parameters = this.serialize(true);
        var comment_container = this.up().previous().down().next();
        if (parameters.comment) {
            comment_container.show();
            submitComment(comment_container, parameters);
            this.elements['comment'].value = '';
        }
    })
}

function unbindExecuteCommentForm(container)
{
    $(container).adjacent('form.comment_form').invoke('stopObserving', 'submit');
}

function changeCaseRunOrder(run_id, case_run_id, sort_key)
{
    nsk = prompt('Enter your new order number', sort_key) // New sort key
    
    if(!nsk)
        return false
   
    if(isNaN(nsk)) {
        alert('The value must be a integer number and limit between 0 to 32300.');
        return false;
    }
    
    if (nsk > 32300 || nsk < 0) {
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
        
        if (returnobj.response == 'ok') {
            window.location.reload();
        } else {
            alert(returnobj.response);
        }
    }
    
    var ctype = 'testruns.testcaserun';
    var object_pk = case_run_id;
    var field = 'sortkey';
    var value = nsk;
    
    updateObject(ctype, object_pk, field, value, s_callback);
}

function taggleSortCaseRun()
{
    if($('id_sort').innerHTML != 'Done Sorting'){
        // $('id_sort_control').show();
        // Remove the unsortable case text
        
        $('id_blind_all_link').remove(); // Remove blind all link
        
        // Remove case text
        $$('#id_table_cases .hide').each(function(t) {
            t.remove();
        });
        
        // Remove blind down arrow link
        $$('#id_table_cases .blind_link').each(function(t) {
            t.remove();
        });
        // Use the title to replace the blind down title link
        $$('#id_table_cases .blind_title_link').each(function(t) {
            t.replace((new Element('span')).update(t.innerHTML));
        });
        
        // Use the sortkey content to replace change sort key link
        $$('#id_table_cases .mark').each(function(t) {
            t.parentNode.update(t.innerHTML);
        });
        
        // init the tableDnD object
        var table = document.getElementById('id_table_cases');
        var tableDnD = new TableDnD();
        tableDnD.init(table);
        $('id_sort').innerHTML='Done Sorting';
        
        //alert('Drag and drop the rows to adjust the order, click "Done Sorting" link to submit your changes, otherwise please refresh the page to cancel.');
    } else {
        // $('id_sort_control').hide();
        $('id_sort').replace((new Element('span')).update('Submitting changes'));
        
        $$('#id_table_cases input[type=checkbox]').each(function(t) {
            t.checked = true;
            t.disabled = false;
        });
        
        window.location.href='ordercaserun/?' + $('id_form_case_runs').serialize();
    }
}
function selectcase(){
    $('testcases_unselected').toggle();
}

function constructCaseRunZone(index_id, url, run_id, case_run_id, parameters, blind_next)
{
    var p = getTestCaseParam(index_id);
    $(p.case_run_container).update('<div class="ajax_loading"></div>');
    
    var complete = function(t) {
        if($('response')) {
            alert($('response').innerHTML);
            return false;
        }
        
        // Bind the display
        unbindExecuteShowCommment('executeList');
        unbindExecuteCommentForm('executeList');
        
        // Bind the display
        bindExecuteShowCommment('executeList');
        bindExecuteCommentForm('executeList');
        
        // Blind down next case content
        var box_is_hidden = $(p.hidenbox).getStyle('display') == 'none'
        if(blind_next) {
            blinddownNextTestCaseContents(index_id);
        } else if (parameters.auto_blinddown == false && box_is_hidden) {
            fireEvent($(p.tr), 'click');
        } else if (!$('id_check_box_auto_blinddown').checked && box_is_hidden) {
            fireEvent($(p.tr), 'click');
        }
    }
    
    var failure = function(t) { 
        alert("Update status failed");
    }
    
    new Ajax.Updater(p.case_run_container, url, {
        method:'get',
        parameters: parameters,
        onComplete: complete,
        onFailure: failure
    });
}

function changeCaseRunStatus(case_run_status_id, status_auto_blinddown, form)
{
    var parameters = form.serialize(true);
    var index_id = parameters.index_id;
    var run_id = parameters.run_id;
    var case_run_id = parameters.case_run_id;
    
    parameters.case_run_status_id = case_run_status_id;
    
    var auto_blinddown = $('id_check_box_auto_blinddown').checked;
    
    if (status_auto_blinddown == '0' || status_auto_blinddown == 'False')
        var status_auto_blinddown = false
    
    if (status_auto_blinddown && auto_blinddown)
        var auto_blinddown = true;
    else
        var auto_blinddown = false;
    parameters.auto_blinddown = auto_blinddown;
    
    var url = '/run/' + run_id + '/caserun/' + case_run_id + '/changestatus/';
    
    constructCaseRunZone(
        index_id, url, run_id, case_run_id, parameters, auto_blinddown
    );
}

function addCaseRunBug(index_id, run_id, case_run_id, case_id)
{
    var p = getTestCaseParam(index_id);
    
    bug_id = prompt('Please input the bug id.');
    bug_id = Trim(bug_id);
    
    if(!bug_id)
        return false
    
    if(!isInteger(bug_id)) {
        alert('Wrong number.');
        return false;
    }
    
    if(bug_id.length > 7) {
        alert('Number too long, length must be less than 7.');
        return false;
    }
    
    var url = '/run/' + run_id + '/caserun/' + case_run_id + '/bug/';
    var parameter = {
        handle: 'add',
        index_id: index_id,
        run: run_id,
        case_run: case_run_id,
        'case': case_id,
        bug_system: 1, // FIXME: Temporary solution here.
        bug_id: bug_id,
    }
    
    constructCaseRunZone(
        index_id, url, run_id, case_run_id, parameter
    );
}
function removeCaseRunBug(index_id, run_id, case_run_id, bug_id, id)
{   
    var p = getTestCaseParam(index_id);
    
    if(!bug_id)
        return false;
    
    if(!confirm('Are you sure to remove the bug?'))
        return false;
    
    var url = '/run/' + run_id + '/caserun/' + case_run_id + '/bug/';
    
    var parameter = {
        handle: 'remove',
        index_id: index_id,
        run: run_id,
        case_run: case_run_id,
        bug_id: bug_id,
        id: id,
    }
    
    constructCaseRunZone(
        index_id, url, run_id, case_run_id, parameter
    );
}


function delCaseRun(run_id)
{
    var response = confirm('Are you sure to delete case run(s) ?');
    
    if(response)
        window.location.href='removecaserun/?' + $('id_form_case_runs').serialize();
}


function editValue(form,hidebox,selectid,submitid)
{
    
    $(hidebox).hide();
    $(selectid).show();
    $(submitid).show();
    
    var data=form.serialize(true);
    var env_property_id = data.env_property_id;
    
    
    var success = function(t){
        returnobj=t.responseText.evalJSON(true);
        
        try {
            console.log('Get environments succeed get ready to replace the select widget inner html');
        } catch(err) {}
        
        var values = returnobj.collect(function(o) {
                           return [o.pk, o.fields.value];
                       })
        
        set_up_choices($(selectid),values,0);
        
        }
        
    var failure = function(t) {
        alert("Update values failed");
    }
    
    var url = '/management/getinfo/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'info_type' : 'env_values',
            'env_property_id': env_property_id,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure,
        });
    
}

function submitValue(run_id,value,hidebox,select_field,submitid){
    
    var new_value = select_field.options[select_field.selectedIndex].innerHTML;
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        if(returnobj.rc == 0){
            
            $(hidebox).innerHTML = new_value;
            
            $(hidebox).show();
            select_field.hide();
            $(submitid).hide();
        } else {
            alert(returnobj.response);
        }
    }
    
    var failure = function(t) {
        alert("Edit value failed");
    }
    
    var url  = '/runs/env_value/';
    new Ajax.Request(url, {
        method:'get',
        parameters: {
            'handle': 'change',
            'old_env_value_id': value,
            'new_env_value_id': select_field.value,
            'run_id' : run_id,
        }, 
        onSuccess: success,
        onFailure: failure
    });
    
    }

function removeProperty(run_id,env_value_id)
{
    if(!confirm('Are you sure to remove this porperty?'))
        return false;
        
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        if(returnobj.rc == 0){
            window.location.reload();
        } else {
            alert(returnobj.response);
        }
    }
    
    var failure = function(t) {
        alert("Edit value failed");
    }
    var url  = '/runs/env_value/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'handle' : 'remove',
            'info_type' : 'env_values',
            'env_value_id' : env_value_id,
            'run_id' : run_id,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure,
        });
    
}

function addProperty(run_id,env_group_id)
{
    
    $('dialog').show();
    $('dialog').update("<div class='add_env_content'><div class='add_env_close' onclick='this.up(1).hide()'></div><div class='env_title' id='id_title_group'></div><div class='add_env_box'>Property<br/><br/><select id='id_add_env_property'></select></div><div class='add_env_box'>Value<br/><br/><select id='id_add_env_value'></select></div><div class='add_env_button'><input type='button' value='Add' id='id_env_add'/><input type='button' value='Reset' onclick='this.up(2).hide()'/></div></div>")
    
    var success = function(t){
        returnobj=t.responseText.evalJSON(true);
        
        
        var values = returnobj.collect(function(o) {
            return [o.pk, o.fields.name];
        })
        
        set_up_choices($('id_add_env_property'),values,0);
        
    }
    
    var failure = function(t) {
        alert("Update properties failed");
    }
    
    var url = '/management/getinfo/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'info_type' : 'env_properties',
            'env_group_id': env_group_id,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure,
        });
    
    
    $('id_add_env_property').observe('change', function(e) {
        change_value($F('id_add_env_property'),'id_add_env_value');
    })
    
    $('id_env_add').observe('click',function(e){
        add_property_to_env(run_id,$F('id_add_env_value'));
    })
    
}

function change_value(env_property_id,selectid)
{
    var success = function(t){
        returnobj=t.responseText.evalJSON(true);
        
        var values = returnobj.collect(function(o) {
            return [o.pk, o.fields.value];
        })
        
        set_up_choices($(selectid),values,0);
    }
        
    var failure = function(t) {
        alert("Update values failed");
    }
    
    var url = '/management/getinfo/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'info_type' : 'env_values',
            'env_property_id': env_property_id,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure,
        });
    
}

function add_property_to_env(run_id,env_value_id)
{
    var success = function(t) {
        returnobj=t.responseText.evalJSON(true);

        if(returnobj.rc == 0) {
            window.location.reload();
        } else {
            alert(returnobj.response);
            return false;
        }
    }
    
    var failure = function(t) {
        alert("Edit value failed");
    }
    var url  = '/runs/env_value/';
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            'handle' : 'add',
            'info_type' : 'env_values',
            'env_value_id' : env_value_id,
            'run_id' : run_id,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure,
    });
}

function addRunTag(container, run_id)
{
    tag = prompt('Please type new tag.');
    if(!tag)
        return false
    
    $(container).update('<div class="ajax_loading"></div>');
    
    var url = new String('/management/tags/');
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: {
            handle: 'add',
            run: run_id,
            tags: tag,
        },
    })
}


function removeRuntag(container, run_id, tag)
{
    $(container).update('<div class="ajax_loading"></div>');
    
    var url = new String('/management/tags/');
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: {
            handle: 'remove',
            run: run_id,
            tags: tag,
        },
    })
}

function constructRunCC(container, run_id, parameters)
{
    var complete = function(t) {
        if($('message')) {
            alert($('message').innerHTML);
            return false;
        }
    }
    var url = new String('/run/' + run_id + '/cc/');
    
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
}

function addRunCC(run_id, container)
{
    user = prompt('Please type new email or username for CC.');
    if(!user)
        return false;
    var parameters = {
        'do': 'add',
        user: user,
    };
    
    constructRunCC(container, run_id, parameters)
}

function removeRunCC(run_id, user, container)
{
    c = confirm('Are you sure to delete this user from CC?');
    
    if(!c)
        return false;
    
    var parameters = {
        'do': 'remove',
        user: user,
    };
    
    constructRunCC(container, run_id, parameters)
}

function changeCaseRunAssignee(form)
{
    var p = prompt('Please type new email or username for assignee');
    if(!p)
        return false;
    
    var parameters = {
          'info_type': 'users',
          'email__startswith': p,
    }
    
    getInfoAndUpdateObject(
        parameters,
        'testruns.testcaserun',
        form.serialize(true).case_run,
        'assignee'
    )
}
