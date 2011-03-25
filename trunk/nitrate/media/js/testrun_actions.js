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
    
    if($('relativeSearchOption_case')) {
        $('relativeSearchOption_case').observe('click', function(e) {
            if($('relativeSearch_case').getStyle('display') == 'none'){
                Effect.BlindDown('relativeSearch_case',{ duration: 0.5 });
                this.className = 'up';
            } else {
                Effect.BlindUp('relativeSearch_case',{ duration: 0.5 });
                this.className = 'down';
            };
        });
    };
    
    if($('testruns_table')) {
        $('id_check_all_runs').observe('click',function(e) {
            clickedSelectAll(this, 'testruns_table', 'run')
        });
        
        TableKit.Sortable.init('testruns_table',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'  
        });
    };
    
    $('id_search_people').name = $F('id_people_type');
    
    $('id_people_type').observe('change', function() {
        $('id_search_people').name = $F('id_people_type');
    });
    
    if($('run_column_add')) {
        $('run_column_add').observe('change', function(t) {
            switch(this.value) {
                case 'col_plan':
                    $('col_plan_head').show();
                    $$('.col_plan_content').each(function(t){ t.show() });
                    $('col_plan_option').hide();
                    break;
            };
        });
    };
	
}

Nitrate.TestRuns.Details.on_load = function()
{
    // Observe the interface buttons
    if($('id_sort'))
        $('id_sort').observe('click', taggleSortCaseRun);
    
    $('id_check_all_button').observe('click', function(e) {
        toggleAllCheckBoxes(this, 'id_table_cases', 'case_run');
    })
    
    
    if($('id_check_box_highlight').checked)
        $$('.mine').invoke('addClassName','highlight');
    
    $('id_check_box_highlight').observe('click', function(e) {
        e=$$('.mine');
        this.checked && e.invoke('addClassName','highlight') || e.invoke('removeClassName','highlight')
    });
    
    $('id_blind_all_link').observe('click', function(e) {
    	//Adding a lock here to avoid generating too much requests.
    	//The lock won't be released until after all requests generated by 'expand all' are finished.
    	//Unfortunately we're using $$('td[id^="id_loading_"]').length == 0.
    	//Not elegant enough.
    	//See https://bugzilla.redhat.com/show_bug.cgi?id=676590
    	if ($$('td[id^="id_loading_"]').length == 0){
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
    
    // Observe the case run toggle and the comment form
    var toggle_case_run = function(e) {
        var c = this.up(); // Container
        var c_container = c.next(); // Content Containers
        var case_id = c.getElementsBySelector('input[name="case"]')[0].value;
        var case_run_id = c.getElementsBySelector('input[name="case_run"]')[0].value;
        var case_text_version = c.getElementsBySelector('input[name="case_text_version"]')[0].value;
        var type = 'case_run';
        var callback = function(t) {
            // Observe the update case run stauts/comment form
            c_container.adjacent('.update_form').invoke('stopObserving', 'submit');
            c_container.adjacent('.update_form').invoke('observe', 'submit', updateCaseRunStatus);
            
            // Observe the delete comment form
            var refresh_case = function(t) {
                constructCaseRunZone(c_container, c, case_id);
            }
            
            var rc_callback = function(e) {
                e.stop();
                if(!confirm(default_messages.confirm.remove_comment))
                    return false;
                removeComment(this, refresh_case)
            };
            c_container.adjacent('.form_comment').invoke('stopObserving', 'submit');
            c_container.adjacent('.form_comment').invoke('observe', 'submit', rc_callback);
        }
        toggleTestCaseContents(type, c, c_container, case_id, case_text_version, case_run_id, callback);
    }
    $$('.expandable').invoke('observe', 'click', toggle_case_run);
    
    // Auto show the case run contents.
    if(window.location.hash != '') {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    } else {
        if($$('tr.is_current').length != 0) {
            $$('tr.is_current').each(function(e) {
                fireEvent(e, 'click');
            });
        };
    };
    
    // Mass operations
    if($('id_mass_change_case_run_status')) {
        $('id_mass_change_case_run_status').observe('change', function(e) {
            var object_pks = serializeCaseRunFromInputList($('id_table_cases'));
            debug_output(this.value);
            if(this.value == '')
                return false;
            if(object_pks.length == 0) {
                alert(default_messages.alert.no_case_selected);
                return false;
            };
            if(!confirm(default_messages.confirm.change_case_status))
                return false;
            updateObject('testruns.testcaserun', object_pks, 'case_run_status', this.value, 'int', reloadWindow);
        });
    };

    // Filter Case-Run
    if($('filter_case_run')) {
            $('filter_case_run').observe('click',function(e){
                if($('id_filter').getStyle('display') == 'none'){
                    $('id_filter').show();
                    this.update(default_messages.link.hide_filter);
                } else {
                    $('id_filter').hide();
                    this.update(default_messages.link.show_filter);
                };
        });
    };
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
    $$('.case_title').invoke('observe', 'click', function(e) {
        var type = 'execute_case_run';
        var container = this.up();
        var content_container = this.next();
        var case_id = this.adjacent('input[name="case_id"]')[0].value;
        var case_text_version = this.adjacent('input[name="case_text_version"]')[0].value;
        var case_run_id = this.adjacent('input[name="case_run_id"]')[0].value;
        var callback = function(t) {
            content_container.getElementsBySelector('.update_form')[0].observe(
                'submit', updateCaseRunStatus
            );
        }
        
        toggleTestCaseContents(type, container, content_container, case_id, case_text_version, case_run_id, callback)
    });
    
    // Auto show the case contents.
    if(window.location.hash != '') {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    } else {
        if($$('.is_current') != []) {
            $$('.is_current').each(function(e) {
                fireEvent(e, 'click');
            })
        }
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
    
    var container = this.up(4);
    var parent = container.up();
    var title = parent.previous();
    var link = title.getElementsBySelector('.expandable')[0];
    var parameters = this.serialize(true);
    var ctype = parameters['content_type'];
    var object_pk = parameters['object_pk'];
    var field = parameters['field'];
    var value = parameters['value'];
    var vtype = 'int';
    
    // Callback when 
    var callback = function(t, rtobj) {
        // Reset the content to loading
        var ajax_loading = getAjaxLoading();
        ajax_loading.id = 'id_loading_' + parameters['case_id'];
        container.update(ajax_loading);
        
        // Update the contents
        if (parameters['value'] != '') {
            // Update the case run status icon
            var crs = Nitrate.TestRuns.CaseRunStatus;
            var icon_status = title.getElementsBySelector('.icon_status');
            icon_status.each(function(item) {
                for (i in crs) {
                    if (typeof(crs[i]) == 'string' && item.hasClassName('btn_' + crs[i]))
                        item.removeClassName('btn_' + crs[i]);
                }
                item.addClassName('btn_' + Nitrate.TestRuns.CaseRunStatus[value-1]);
            })
            
            // Update related people
            var usr = Nitrate.User;
            title.getElementsBySelector('.link_tested_by').each(function(i) {
                i.href = 'mailto:' + usr.email;
                i.update(usr.username);
            })
        }
        
        // Mark the case run to mine
        if(!title.hasClassName('mine'))
            title.addClassName('mine');
        
        // Blind down next case
        fireEvent(link, 'click');
        if ($('id_check_box_auto_blinddown').checked && parameters['value'] != '') {
            var next_title = parent.next();
            if(!next_title) {
                alert(default_messages.alert.last_case_run);
                return false;
            }
            if(next_title.next().getStyle('display') == 'none')
                fireEvent(next_title.getElementsBySelector('.expandable')[0], 'click');
        } else {
            fireEvent(link, 'click');
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
        // updateObject(ctype, object_pk, 'close_date', 'NOW', 'datetime');
        updateObject(ctype, object_pk, field, value, vtype, callback);
        
        /*
        if(parameters['assignee'] != Nitrate.User.pk)
            updateObject(ctype, object_pk, 'assignee', Nitrate.User.pk);
        if(parameters['tested_by'] != Nitrate.User.pk)
            updateObject(ctype, object_pk, 'tested_by', Nitrate.User.pk);
        */
        // Set the case run to be current
        // new Ajax.Request(getURLParam(object_pk).url_case_run_set_current);
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
    var vtype = 'int';
    
    updateObject(ctype, object_pk, field, value, vtype, s_callback);
}

function taggleSortCaseRun(event)
{
    var element = event.target;
    
    if(element.innerHTML != 'Done Sorting'){
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
        // var element = element.replace((new Element('span')).update('Submitting changes'));
        
        $$('#id_table_cases input[type=checkbox]').each(function(t) {
            t.checked = true;
            t.disabled = false;
        });
        postToURL('ordercaserun/', serializeCaseRunFromInputList(element.up(2).next().next(), 'case_run'), 'get');
    }
}
function selectcase(){
    $('testcases_unselected').toggle();
}

function constructCaseRunZone(container, title_container, case_id)
{
    var link = title_container.getElementsBySelector('.expandable')[0];
    if(container) {
        var td = new Element('td', {'id': 'id_loading_' + case_id, 'colspan': 12});
        td.update(getAjaxLoading());
        container.update(td);
    }
    
    if(title_container) {
        fireEvent(link, 'click');
        fireEvent(link, 'click');
    }
}

function addCaseRunBug(title_container, container, case_id, case_run_id, callback)
{
    // FIXME: Popup dialog to select the bug system
    bug_id = prompt('Please input the bug id.');
    bug_id = bug_id.replace(/ /g, '');
    
    if(!bug_id)
        return false
    
    if(parseInt(bug_id) != bug_id) {
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
function removeCaseRunBug(title_container, container, bug_id, case_id, case_run_id, callback)
{   
    if(!bug_id)
        return false;
    
    if(!confirm('Are you sure to remove the bug?'))
        return false;
    
    var url = '/caserun/' + case_run_id + '/bug/';
    
    var parameters = {
        a: 'remove',
//        index_id: index_id,
//        run: run_id,
        case_run: case_run_id,
        bug_id: bug_id,
    }
    
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


function delCaseRun(run_id)
{
    if(confirm('Are you sure to delete case run(s) ?'))
       postToURL('removecaserun/', serializeCaseRunFromInputList('id_table_cases', 'case_run'));
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
        
        debug_output('Get environments succeed get ready to replace the select widget inner html');
        
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
    $('dialog').update("<div class='add_env_content'><div class='add_env_close' onclick='this.up(1).hide()'></div><div class='env_title' id='id_title_group'></div><div class='add_env_box'>Property<br/><br/><select id='id_add_env_property'></select></div><div class='add_env_box'>Value<br/><br/><select id='id_add_env_value'></select></div><div class='add_env_button'><input type='button' value='Add' id='id_env_add'/><input type='button' value='Cancel' onclick='this.up(2).hide()'/></div></div>")
    
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

function changeCaseRunAssignee()
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
        serializeCaseRunFromInputList($('id_table_cases')),
        'assignee'
    )
}

function serializeCaseRunFromInputList(table, name)
{
    var elements = $(table).adjacent('input[name="case_run"]:checked');
    var returnobj_list = new Array();
    for (i in elements) {
        if (typeof(elements[i].value) == 'string')
        returnobj_list.push(elements[i].value);
    };
    if (name) {
        var returnobj = {};
        returnobj[name] = returnobj_list
        return returnobj
    }
    
    return returnobj_list;
}

function serialzeCaseForm(form, table, serialized)
{
    if(typeof(serialized) != 'boolean')
        var serialized = true;
    var data = form.serialize(serialized);
    data['case_run'] = serializeCaseFromInputList(table);
    return data
}

function sortCaseRun(form, order)
{
    if (form.order_by.value == order)
        form.order_by.value = '-' + order;
    else
        form.order_by.value = order;
    fireEvent(form.getElementsBySelector('input[type="submit"]')[0], 'click');
}

function showCaseRunsWithSelectedStatus(form, status_id)
{
    form.case_run_status__pk.value = status_id;
    fireEvent(form.getElementsBySelector('input[type="submit"]')[0], 'click');
}

/*
Functions defined below are using jQuery.
Author: ctang@redhat.com - 22 March 2011 
*/

function updateBugs(action){
    var bug_ids = prompt("Specify bug IDs, using comma to seperate multiple IDs.");
    if(!bug_ids){
        alert(default_messages.alert.no_bugs_specified);
        return false;
    }
    var runs = serializeCaseRunFromInputList($('id_table_cases'));
    if(!runs){
        alert(default_messages.alert.no_case_selected);
        return false;
    }
    jQ.ajax({
        url: '/caserun/update-bugs-for-many/',
        success: reloadWindow,
        data: {
            'bugs': bug_ids,
            'action': action,
            'runs': runs.join(),
            'bug_system': 1
        }
    });
}

function showCommentForm(){
    var dialog = getDialog();
    var comment_form = '<ul>' +
                            '<li><b>Comments: </b></li>' +
                            '<li><textarea name="comments" id="commentText" style="width:100%;height:100px;"></textarea></li>' + 
                            '<li><button id="btnComment">Confirm</button> <button id="btnCancelComment">Cancel</button>' +
                            ' <span id="commentsErr"></span>' +
                        '</ul>';
    dialog.update(comment_form);
    var commentText = jQ('#commentText');
    var commentsErr = jQ('#commentsErr');
    jQ('#btnComment').live('click', function(){
        var error;
        var comments = jQ.trim(commentText.val());
        var runs = serializeCaseRunFromInputList($('id_table_cases'));
        if(!comments)
            error = 'No comments given.';
        if(!runs)
            error = default_messages.alert.no_case_selected;
        if(error){
            commentsErr.html(error);
            return false;
        }
        jQ.ajax({
            url: '/caserun/comment-many/',
            data: {'comment': comments, 'run': runs.join()},
            dataType: 'json',
            success: function(res){
                if(res.rc==0){
                    reloadWindow();
                }else{
                    commentsErr.html(res.response);
                    return false;
                }
            }
        });
    });
    jQ('#btnCancelComment').live('click', function(){
        dialog.hide();
        commentText.val('');
    });
    dialog.show();
}

function commentCaseRuns(){
    // comment multiple caseruns at a time.

    dialog.update();
    dialog.show();
    
}

jQ(document).ready(function(){
    jQ('.btnBlueCaserun').mouseover(function(){
        jQ(this).find('ul').show();
    }).mouseout(function(){
        jQ(this).find('ul').hide();
    });
    jQ('ul.statusOptions a').click(function(){
        var option = jQ(this).attr('value');
        var object_pks = serializeCaseRunFromInputList($('id_table_cases'));
        if(option == '')
            return false;
        if(object_pks.length == 0) {
            alert(default_messages.alert.no_case_selected);
            return false;
        };
        if(!confirm(default_messages.confirm.change_case_status))
            return false;
        updateObject('testruns.testcaserun', object_pks, 'case_run_status', option, 'int', reloadWindow);
    });
    // URL updating bugs: /caserun/update-bugs-for-many/
    // URL commenting bugs: /caserun/comment-many/
});
