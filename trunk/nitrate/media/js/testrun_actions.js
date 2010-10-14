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
        TableKit.Sortable.init('testruns_table',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'  
        });
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
    
    $$('.expandable').invoke('observe', 'click', function(e) {
        var c = this.up(); // Container
        var c_container = c.next(); // Content Containers
        var case_id = c.getElementsBySelector('input[name="case"]')[0].value;
        var case_run_id = c.getElementsBySelector('input[name="case_run"]')[0].value;
        var case_text_version = c.getElementsBySelector('input[name="case_text_version"]')[0].value;
        var type = 'case_run';
        toggleTestCaseContents(type, c, c_container, case_id, case_text_version, case_run_id);
    });
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    }
}

Nitrate.TestRuns.New.on_load = function()
{
    if($('testcases')) {
          TableKit.Sortable.init('testcases',
          {
             nosortClass : 'nosort'
          });
    }
    if($('testcases_filter')) {
        TableKit.Sortable.init('testcases_filter',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'
        });
    }

}

Nitrate.TestRuns.Edit.on_load = function()
{
    bind_version_selector_to_product(false);
    bind_build_selector_to_product(false);
}

Nitrate.TestRuns.Execute.on_load = function()
{
    $$('.execute_case_run').invoke('observe', 'click', function(e) {
        var type = 'execute_case_run';
        var container = this.up();
        var content_container = this.next();
        var case_id = this.getElementsBySelector('input[name="case_id"]')[0].value;
        var case_text_version = this.getElementsBySelector('input[name="case_text_version"]')[0].value;
        var case_run_id = this.getElementsBySelector('input[name="case_run_id"]')[0].value;
        var callback = function(t) {
            content_container.getElementsBySelector('.update_form')[0].observe('submit', updateCaseRunStatus);
        }
        
        toggleTestCaseContents(type, container, content_container, case_id, case_text_version, case_run_id, callback)
    });
    
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
    if($('id_check_box_highlight').checked)
        $$('.mine').invoke('addClassName','highlight');
    
    $('id_check_box_highlight').observe('click', function(e) {
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

var updateCaseRunStatus = function(e)
{
    e.stop();
    var container = this.up(2);
    var parent = container.up();
    var title = container.previous();
    var parameters = this.serialize(true);
    var content_type = parameters['content_type'];
    var object_pk = parameters['object_pk'];
    var field = parameters['field'];
    var value = parameters['value'];

	// Callback when 
    var callback = function(t, rtobj) {
        // Reset the content to loading
        var ajax_loading = getAjaxLoading();
        ajax_loading.id = 'id_loading_' + parameters['case_id'];
        container.update(ajax_loading);
        
        // Update the contents
        if (parameters['value'] != '') {
            var crs = Nitrate.TestRuns.CaseRunStatus;
            var icon_status = parent.getElementsBySelector('.icon_status');
            icon_status.each(function(item) {
                for (i in crs) {
                    if (typeof(crs[i]) == 'string' && item.hasClassName('btn_' + crs[i]))
                        item.removeClassName('btn_' + crs[i]);
                }
                item.addClassName('btn_' + Nitrate.TestRuns.CaseRunStatus[value-1]);
            })
        }
        
        // Mark the case run to mine
        if(!title.hasClassName('mine'))
            title.addClassName('mine');
        
        // Blind down next case
        fireEvent(title, 'click');
        
        if ($('id_check_box_auto_blinddown').checked && parameters['value'] != '') {
            if(!parent.next()) {
                alert(default_messages.alert.last_case_run);
                return false;
            }
            
            if(parent.next().down().next().getStyle('display') == 'none')
                fireEvent(parent.next().down(), 'click');
        } else {
            fireEvent(title, 'click');
        }
    }
    
    // Add comment
    if (parameters['comment'] != '') {
        var c = new Element('div');
        if(parameters['value'] != '')
            submitComment(c, parameters);
        else
            submitComment(c, parameters, callback)
    }
    
    // Update the object when changing the status
    if(parameters['value'] != '') {
        updateObject(content_type, object_pk, 'close_date', 'NOW');
        updateObject(content_type, object_pk, field, value, callback);
        
        if(parameters['assignee'] != Nitrate.User.pk)
            updateObject(content_type, object_pk, 'assignee', Nitrate.User.pk);
        if(parameters['tested_by'] != Nitrate.User.pk)
            updateObject(content_type, object_pk, 'tested_by', Nitrate.User.pk);
        
        // Set the case run to be current
        new Ajax.Request(getURLParam(object_pk).url_case_run_set_current);
    }
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
        $$('#id_table_cases .blind_icon').each(function(t) {
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
        
        $$('#id_table_cases .case_content').invoke('remove');
        $$('#id_table_cases .expandable').invoke('stopObserving');
        
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

function constructCaseRunZone(container, title_container, case_id)
{
    if(container) {
        var ajax_loading = getAjaxLoading();
        ajax_loading.id = 'id_loading_' + case_id;
        container.update(ajax_loading);
    }
    
    if(title_container) {
        fireEvent(title_container, 'click');
        fireEvent(title_container, 'click');
    }
}

function addCaseRunBug(title_container, container, case_id, case_run_id, callback)
{
    // FIXME: Popup dialog to select the bug system
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
    
    var url = getURLParam(case_run_id).url_case_run_bug;
    var parameters = {
        a: 'add',
        case_run: case_run_id,
        bug_system: 1, // FIXME: Temporary solution here.
        bug_id: bug_id,
    }
    parameters['case'] = case_id;
    
    var success = function(t) {
        var returnobj = t.responseText.evalJSON();
        
        if(returnobj.rc == 0) {
            if (callback)
                return callback();
            
            return constructCaseRunZone(container, title_container, case_id);
        } else {
            alert(returnobj.response);
            return false;
        }
    }
    
    new Ajax.Request(url, {
        method: 'get',
        parameters: parameters,
        onSuccess: success,
        onFailure: json_failure,
    })
}
function removeCaseRunBug(bug_id, parameters, callback)
{   
    if(!bug_id)
        return false;
    
    if(!confirm('Are you sure to remove the bug?'))
        return false;
    
    var url = '/caserun/' + case_run_id + '/bug/';
    
    var parameter = {
        a: 'remove',
        index_id: index_id,
        run: run_id,
        case_run: case_run_id,
        bug_id: bug_id,
    }
    
   var success = function(t) {
		var returnobj = t.responseText.evalJSON();
		
		if(returnobj.rc == 0) {
			if (callback)
				return callback();
			
			return constructCaseRunZone(container, title_container);
		} else {
			alert(returnobj.response);
			return false;
		}
	}
	
	new Ajax.Request(url, {
		method: 'get',
		parameters: parameters,
		onSuccess: success,
		onFailure: json_failure,
	})
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
            'a': 'change',
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
            'a' : 'remove',
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
            'a' : 'add',
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
            a: 'add',
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
            a: 'remove',
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
