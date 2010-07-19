Nitrate.TestPlans = {};
Nitrate.TestPlans.Create = {};
Nitrate.TestPlans.List = {};
Nitrate.TestPlans.Details = {};
Nitrate.TestPlans.Edit = {};
Nitrate.TestPlans.SearchCase = {};
Nitrate.TestPlans.Clone = {};

Nitrate.TestPlans.Create.on_load = function()
{
    bind_version_selector_to_product(false, $('id_product'), $('id_product_version'));
    // bind_properties_selector_to_product(false, 'id_properties_container');
    $('env_group_help_link').observe('click', function(t) {
        $('env_group_help').toggle();
    })
    $('env_group_help_close').observe('click', function(t) {
        $('env_group_help').hide();
    })
    
}
Nitrate.TestPlans.Edit.on_load = function()
{
    $('env_group_help_link').observe('click', function(t) {
        $('env_group_help').toggle();
    })
    $('env_group_help_close').observe('click', function(t) {
        $('env_group_help').hide();
    })
    bind_version_selector_to_product(false);
}

Nitrate.TestPlans.List.on_load = function()
{
    if($('id_product')) {
        bind_version_selector_to_product(true);
    }
    

    if($('testplans_table')) {
        SortableTable.setup({
            rowEvenClass : 'evenRow',
            rowOddClass : 'oddRow',
            nosortClass : 'nosort'
        });

        SortableTable.init('testplans_table');
    }

    if($('column_add')) {
        $('column_add').observe('change', function(t) {
            switch(this.value) {
                case 'col_product':
                    $('col_product_head').show();
                    $$('.col_product_content').each(function(t){ t.show() });
                    $('col_product_option').hide();
                    break;
                case('col_product_version'):
                    $('col_product_version_head').show();
                    $$('.col_product_version_content').each(function(t){ t.show() });
                    $('col_product_veresion_option').hide();
                    break;
            }
        })
    }
    
    $$('input[name="plan_id"]').each(function(e){
        e.observe('click', function(t) {
            if(e.checked) {
                e.up(1).addClassName('selection_row');
            } else {
                e.up(1).removeClassName('selection_row');
            }
        })
    })
    
}

Nitrate.TestPlans.Details.on_load = function()
{
    if($F('id_plan_id'))
        plan_id = $F('id_plan_id');
    else {
        alert('Can not get the plan id');
        return false;
    }
    
    
    // regUrl('display_summary');
    
    constructPlanDetailsCasesZone('testcases', plan_id);
    constructTagZone('tag', { plan: plan_id });
    constructPlanComponentsZone('components');
    
    SortableTable.init('testruns_table');
    SortableTable.init('testreview_table');
    
    $$('li.tab a').invoke('observe', 'click', function(i) {
        $$('div.tab_list').each(function(t) {
            t.hide();
        })
        
        $$('li.tab').each(function(t) {
            t.removeClassName('tab_focus');
        })
        this.parentNode.addClassName('tab_focus');
        
        $(this.title).show();
    })
    
    if(window.location.hash) {
        fireEvent($$('a[href=\"' + window.location.hash + '\"]')[0], 'click');
    }

    if($('btn_disable')) {
        $('btn_disable').observe('click',function(e){
            var callback = function() {
                window.location.reload(true);
            }
            updateObject('testplans.testplan', plan_id, 'is_active', 0, callback);
        })
    }

    if($('btn_enable')) {
        $('btn_enable').observe('click',function(e){
            var callback = function() {
                window.location.reload(true);
            }
            updateObject('testplans.testplan', plan_id, 'is_active', 1, callback);
        })
    }
};

Nitrate.TestPlans.SearchCase.on_load = function()
{
    if($('id_product')) {    
        if($F('id_product') != "")
        {
            bind_category_selector_to_product(true, true, $('id_product'), $('id_category'));
            bind_component_selector_to_product(true, true, $('id_product'), $('id_component'));
            // bind_version_selector_to_product(true);
        }
    }
}

Nitrate.TestPlans.Clone.on_load = function()
{
    bind_version_selector_to_product(false);
    
    $('id_link_testcases').observe('change', function(e) {
        if(this.checked) {
            this.parentNode.parentNode.className = 'choose';
            $('id_clone_case_zone').style.display = 'block';
        } else {
            this.parentNode.parentNode.className = 'unchoose';
            $('id_clone_case_zone').style.display = 'none';
        }
    })
    
    $('id_copy_testcases').observe('change', function(e){
        if(this.checked) {
            $('id_maintain_case_orignal_author').disabled = false;
            $('id_keep_case_default_tester').disabled = false;
        } else {
            $('id_maintain_case_orignal_author').disabled = true;
            $('id_keep_case_default_tester').disabled = true;
        }
    })
}

function getTestPlanParam()
{
    var param = new Array();
    param[0] = 'title';
    param[1] = 'product';
    // (product_version/version_id is a special case)
    param[3] = 'type';
    param[4] = 'summary';
    return param;
}

function switchToEditPlanMode()
{
    args = $A(arguments);
    plan_id = args[0];
    
    objs = getTestPlanParam();
    $A(objs).each(function(name) {
        $('display_' + name).hide();
        $('form_' + name).show();
    })
    // Version editing is a special case:
    $('display_product_version').hide();
    $('form_version_id').show();
    
    $('control_box').appear();
    $('btn_edit').href = "javascript:switchToPlanNormalDisplayMode(" + plan_id + ")";
    // $('btn_edit').innerHTML = "Save";
    $('id_buttons').hide();
    $('title_id').show();
    $('form_upload_plan_summary').show()
    $('form_upload_plan_summary').down().style.overflow = ""
    if($('display_summary_short')) {
        $('id_link_show_more').hide();
        $('display_summary_short').hide();
    }
}

function switchToPlanNormalDisplayMode()
{
    args = $A(arguments);
    plan_id = args[0];
    
    objs = getTestPlanParam();
    $A(objs).each(function(name) {
        $('form_' + name).hide();
        $('display_' + name).show();
    })
    // Version editing is a special case:
    $('form_version_id').hide();
    $('display_product_version').show();
    
    // saveModifiedTestPlan(plan_id);
    
    $('control_box').hide();
    $('btn_edit').href = "javascript:switchToEditPlanMode(" + plan_id + ")";
    // $('btn_edit').innerHTML = "Edit";
    $('id_buttons').show();
    $('title_id').hide();
    $('form_upload_plan_summary').hide()
    
    showMoreSummary();
}

function showTab(tab_id)
{
    /*
    $$('li.tab').each(function(t){
        t.removeClassName("tab_focus")
    })
    $('tab_'+tab_id).addClassName ("tab_focus");
    $$('div.tab_list').each(function(s){
        s.hide();
    })
    $(tab_id).show();
    */
}

function showMoreSummary()
{
    $('display_summary').show();
    if($('display_summary_short')) {
        $('id_link_show_more').hide();
        $('id_link_show_short').show();
        $('display_summary_short').hide();
    }
}

function showShortSummary()
{
    $('id_link_show_more').show();
    $('display_summary').hide();
    if($('display_summary_short')) {
        $('id_link_show_short').hide();
        $('display_summary_short').show();
    }
    
    window.scrollTo(0, 0);
}

function createUploadPlanSummaryZone()
{
    try {
        console.log('Successd to hook with the upload plan summary button');
    } catch(err) {}

    new Ajax_upload($('id_btn_upload_plan_summary'), {
        action: '/plan/new/uploadsummary/',
        name: 'plan_summary',

        onSubmit: function(file, extension) {
            try {
                console.log('Upload plan document success submit');
            } catch(err) {}
            
            if (! (extension && /^(txt|html|htm)$/.test(extension))) {
                        // extension is not allowed
                        alert('Error: invalid file extension, only allow .txt, .htm, or .html file upload.');
                        // cancel upload
                        return false;
            }
            
            $('id_btn_upload_plan_summary').disable();
            $('id_btn_upload_plan_summary').value = "Uploading, please wait..."
        },

        onComplete: function(file, response) {
            returnobj = response.evalJSON(true);
            summary = decodeURI(returnobj.summary);

            try {
                console.log("1" + returnobj.response);
                console.log("2" + summary);
            } catch(err) {}

            if(returnobj.response == 'ok') {
                if(tinyMCE.get('id_summary'))
                    tinyMCE.get('id_summary').setContent(summary);
                else
                    $('id_summary').value = summary;
                    
                $('id_btn_upload_plan_summary').enable();
                $('id_btn_upload_plan_summary').value = "Upload plan document..."
            } else {
                alert("Upload document failed, please try again or contact to admin.");
                $('id_btn_upload_plan_summary').enable();
                $('id_btn_upload_plan_summary').value = "Upload plan document..."
            }
        }
    });
}

function taggleSort() { 
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
        
        // Remove change status link, default the link is hidden
        $$('#id_table_cases .show_change_status_link').each(function(t) {
            t.remove();
        });
        
        // Use the selector content to replace the selector
        $$('#id_table_cases .change_status_selector').each(function(t) {
            var w = t.selectedIndex;
            t.replace((new Element('span')).update(t.options[w].text));
        });
        
        // Use the title to replace the blind down title link
        $$('#id_table_cases .blind_title_link').each(function(t) {
            t.replace((new Element('span')).update(t.innerHTML));
        });
        
        // Use the sortkey content to replace change sort key link
        $$('#id_table_cases .mark').each(function(t) {
            t.update(t.down().innerHTML);
        });
        
        // init the tableDnD object
        var table = document.getElementById('id_table_cases');
        var tableDnD = new TableDnD();
        tableDnD.init(table);
        $('id_sort').innerHTML='Done Sorting';
        $$('#id_table_cases td').invoke('addClassName', 'cursor_move');
        //alert('Drag and drop the rows to adjust the order, click "Done Sorting" link to submit your changes, otherwise please refresh the page to cancel.');
    } else {
        // $('id_sort_control').hide();
        $('id_sort').replace((new Element('span')).update('...Submitting changes'));
        
        $$('#id_table_cases input[type=checkbox]').each(function(t) {
            t.checked = true;
            t.disabled = false;
        });
        
        var parameters = $('id_form_cases').serialize(true);
        parameters.a = 'order_cases';
        postToURL('cases/', parameters)
    }
}

function delPlanCase(container, plan_id) 
{
    var parameters = $('id_form_cases').serialize(true);
    parameters.a = 'delete_cases';
    
    if(!parameters['case']) {
        alert('At least one case is required to delete.');
        return false;
    }
    
    var test = confirm("Are you sure to remove test case(s) from this test plan?")
    if (test && $('id_form_cases')) {
        var success = function(t) {
            returnobj = t.responseText.evalJSON(true);
            
            if(returnobj.response == 'ok') {
                parameters.a = 'initial';
                constructPlanDetailsCasesZone(container, plan_id, parameters);
                return true;
            }
            
            alert(returnobj.response);
        }
        
        var failure = function(t) {
            alert('Remove failed');
            return false;
        }
        
        var url = new String('cases/');
        new Ajax.Request(url, {
            method: 'get',
            parameters: parameters,
            onSuccess: success,
            onFailure: failure
        })
    }
}

function constructPlanDetailsCasesZone(container, plan_id, parameters)
{
    $(container).update('<div class="ajax_loading"></div>');
    
    if(!parameters)
        var parameters = {'a': 'initial', 'from_plan': plan_id}
    
    complete = function(t) {
        new Draggable('id_import_case_zone');
        
        $('id_form_cases').observe('submit', function(e) {
            e.stop();
            var p = this.serialize();
            constructPlanDetailsCasesZone(container, plan_id, p);
        })
        
        if($('id_sort'))
            $('id_sort').observe('click', taggleSort); 
        // $('case_new_selector').observe('onchange',newcase);
        
        /*
        $('filter_priority_trigger').observe('click', function(m){
            $('filter_priority').toggle();
        });
        */
        
        $('id_filtercase').observe('click', function(t) {
            var element = $('list_filter_m');
            if(element.getStyle('display') == 'none'){
                element.show();
                this.update(default_messages.link.hide_filter);
            } else {
                element.hide();
                this.update(default_messages.link.show_filter);
            }
        })
        
        
        $$('input[name="case"]').invoke('observe', 'click', function(t) {
            if(this.checked) {
                this.up(1).addClassName('selection_row');
            } else {
                this.up(1).removeClassName('selection_row');
            }
        })
        
        $('new_case_set_status').observe('change',function(t) {
            if(!this.value)
                return false;
            
            if(!$('id_form_cases').serialize(true)['case']){
                alert(default_messages.alert.no_case_selected);
                return false;
            }
            
            var c = confirm(default_messages.confirm.change_case_status);
            if(!c)
                return false;
            
            var parameters = $('id_form_cases').serialize(true);
            
            var s_callback = function(t) {
                returnobj = t.responseText.evalJSON(true);
                
                if(returnobj.rc == 0) {
                    constructPlanDetailsCasesZone(container, plan_id, parameters);
                } else {
                    alert(returnobj.response);
                    return false;
                }
            }
            
            changeCaseStatus(parameters['case'], this.value, s_callback);
        })
        
        $('new_case_priority').observe('change', function(t) {
            if(!this.value)
                return false;
            
            if(!$('id_form_cases').serialize(true)['case']){
                alert(default_messages.alert.no_case_selected);
                return false;
            }
            
            var c=confirm(default_messages.confirm.change_case_priority)
            if(!c)
                return false;
            
            var parameters = $('id_form_cases').serialize(true);
            
            var s_callback = function(t) {
                returnobj = t.responseText.evalJSON(true);
                
                if(returnobj.rc == 0) {
                    constructPlanDetailsCasesZone(container, plan_id, parameters);
                } else {
                    alert(returnobj.response);
                    return false
                }
            }
            
            changeCasePriority(parameters['case'], this.value, s_callback);
        })
        
        // Observe the batch case automated status button
        $('batch_automated').observe('click', function(e) {
            if(!$('id_form_cases').serialize(true)['case']){
                alert(default_messages.alert.no_case_selected);
                return false;
            }
            
            $('dialog').update('<div class="ajax_loading"></div>');
            $('dialog').show();
            
            // Generate the contents of dialog
            var form_content = '<form id="id_form_batch_automated" action="/cases/automated/" method="get"><div class="dia_title" style=" margin:30px 20px;">Please select automation status:</div><div class="dia_content" style=" margin:30px 20px;">';
            form_content += '<div id="id_automated_form"><div class="ajax_loading"></div></div>';
            form_content += '</div><div id="id_form_batch_autoated_actions" style="margin:30px 20px; display:none;"><input type="submit" value="Submit"><input type="button" value="Cancel" onclick="this.up(2).hide();"></div></div></form>';
            $('dialog').update(form_content);

            // Callback for getForm, it will display the submit buttons for the form
            var parameters = {'a': 'change',}
            var callback = function(e) {
                $('id_form_batch_autoated_actions').show();
            }
            getForm(
                'id_automated_form', 'testcases.CaseAutomatedForm', parameters, callback
            );

            // Observe the batch automated form submit event
            // Change the automated status for selected cases
            $('id_form_batch_automated').observe('submit', function(e) {
                e.stop();
                
                var parameters = this.serialize(true);
                parameters['case'] = $('id_form_cases').serialize(true)['case'];

                // Hard code to determine the parameters here.
                /*
                // FIXME: Always return false here.
                if(!parameters['case'] || !parameters['o_is_automated'] || !parameters['o_is_automated_proposed'])
                    return false;
                */
                
                var success = function(t) {
                    returnobj = t.responseText.evalJSON(true);

                    if (returnobj.rc != 0) {
                        var errors = '';
                        returnobj.response.each(function(m) {
                            errors += m[0] + ': ' + m[1] + "\n";
                        });
                        alert(errors);
                        return false;
                    }
                    
                    parameters = $('id_form_cases').serialize(true);
                    parameters.a = 'initial';
                    constructPlanDetailsCasesZone(container, plan_id, parameters);
                    $('dialog').hide();
                }
                
                new Ajax.Request(getURLParam().url_cases_automated, {
                    method: 'post',
                    parameters: parameters,
                    onSuccess: success,
                });
            });
        })
        
        // Observe the batch add case button
        $('id_add_case_tags').observe('click',function(e) {
            if(!$('id_form_cases').serialize(true)['case']){
                alert(default_messages.alert.no_case_selected);
                return false;
            }
            
            constructBatchTagProcessDialog();
            
            // Observe the batch tag form submit
            $('id_batch_tag_form').observe('submit',function(e){
                e.stop();
                var parameters = this.serialize(true);
                parameters['case'] = $('id_form_cases').serialize(true)['case'];
                if(!parameters.tags)
                    return false;
                                
                // Callback for display the cases that just added tags
                var c = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    $('dialog').hide('');
                    $('dialog').update('');
                    $('dialog').show();
                    var html = '<div class="dia_title" style=" margin:10px 20px;">You have successfully add <span class="red">'+ parameters.tags + '</span>&nbsp;in the following case:</div><div class="dialog_content">';
                    $('dialog').update(html);
                    
                    returnobj.each(function(i) {
                        html += '<div class="dia_content" style=" margin:10px 20px;">'+i.pk + ' &nbsp; ' + i.fields.summary+'</div>';
                    });
                    $('dialog').update(html);
                    
                    html +='</div><input class="dia_btn_close sprites" onclick="this.up(0).hide()" type="button" value="Close" style=" margin:10px 20px;"/>';
                    
                    $('dialog').update(html);
                    p = $('id_form_cases').serialize(true);
                    p.a = 'initial';
                    constructPlanDetailsCasesZone(container, plan_id, p);
                };
                var format = 'serialized';
                addBatchTag(parameters, c, format);
            })
        })

        // Observe the batch remove tag function
        $('id_remove_case_tags').observe('click',function(e) {
            if(!$('id_form_cases').serialize(true)['case']){
                alert(default_messages.alert.no_case_selected);
                return false;
            }
            
            constructBatchTagProcessDialog();
            
            // Observe the batch tag form submit
            $('id_batch_tag_form').observe('submit',function(e){
                e.stop();
                var parameters = this.serialize(true);
                parameters['case'] = $('id_form_cases').serialize(true)['case'];
                if(!parameters.tags)
                    return false;
                                
                // Callback for display the cases that just added tags
                var c = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    $('dialog').hide('');
                    $('dialog').update('');
                    $('dialog').show();
                    var html = '<div class="dia_title" style=" margin:10px 20px;">You have successfully remove <span class="red">'+ parameters.tags + '</span>&nbsp;in the following case:</div><div class="dialog_content">';
                    $('dialog').update(html);
                    
                    returnobj.each(function(i) {
                        html += '<div class="dia_content" style=" margin:10px 20px;">'+i.pk + ' &nbsp; ' + i.fields.summary+'</div>';
                    });
                    $('dialog').update(html);
                    
                    html +='</div><input class="dia_btn_close sprites" onclick="this.up(0).hide()" type="button" value="Close" style=" margin:10px 20px;"/>';
                    
                    $('dialog').update(html);
                    p = $('id_form_cases').serialize(true);
                    p.a = 'initial';
                    constructPlanDetailsCasesZone(container, plan_id, p);
                };
                var format = 'serialized';
                removeBatchTag(parameters, c, format)
             })
        
        })
        
        // Bind click the tags in tags list to tags field in filter
        $$('#id_case_own_tags_list a[href="#testcases"]').invoke('observe', 'click',
            function(e) {
                if($('list_filter_m').style.display == 'none')
                    fireEvent($('id_filtercase'), 'click');
                
                addItemsToTextBoxAsList(this.innerHTML, $('id_form_cases').tag__name__in);
            }
        )
    }
    
    var url = getURLParam().url_search_case;
    new Ajax.Updater(container, url, {
        method: 'post',
        parameters: parameters,
        onComplete: complete,
        onFailure: json_failure
    })
    
}

function constructPlanComponentsZone(container, parameters, callback)
{
    if(!parameters)
        var parameters = {
            plan: Nitrate.TestPlans.Instance.pk,
        }
    
    var url = getURLParam().url_plan_components;
    
    var complete = function(t) {
        if(callback) {
            callback();
        }
        
        $('id_form_plan_components').observe('submit', function(e) {
            e.stop();
            var p = this.serialize(true);
            constructPlanComponentsZone(container, p, callback);
        });
        
        $$('.link_remove_plan_component').invoke('observe', 'click', function(e) {
            var links = $$('.link_remove_plan_component');
            var index = links.indexOf(this);
            var component = $$('input[type="checkbox"][name="component"]')[index];
            
            var p = $('id_form_plan_components').serialize(true);
            p['component'] = component.value;
            p['a'] = 'remove';
            
            constructPlanComponentsZone(container, p, callback)
        })
    }
    
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
        onFailure: html_failure,
    })
}

function constructPlanComponentModificationDialog(container)
{
    if(!container)
        var container = getDialog();
    container.show();
    
    var f = new Element('form', {'action': getURLParam().url_plan_components});
    var s = new Element('input', {'type': 'submit', 'name': 'a', 'value': 'Update'}); // Submit button
    var c = new Element('input', {'type': 'button', 'value': 'Cancel'}); // Cancel button
    
    var parameters = {
        a: 'get_form',
        plan: Nitrate.TestPlans.Instance.pk,
    };
    
    f.observe('submit', function(e) {
        e.stop();
        constructPlanComponentsZone('components', this.serialize());
        clearDialog();
    })
    
    c.observe('click', function(e) {
        clearDialog();
    })
    
    var callback = function(t) {
        container.update(f);
        f.appendChild(s);
        f.appendChild(c);
        
        // FIXME: Split the select to two columns, javascript buggy here.
        /*
        SelectFilter.init("id_component", "component", 0, "/admin_media/");
        refreshSelectFilter('component');
        */
    }
    
    // Get the form and insert into the dialog.
    constructPlanComponentsZone(f, parameters, callback);
}

function constructBatchTagProcessDialog(){
    $('dialog').show();
    $('dialog').update('<form id="id_batch_tag_form"><div class="dia_title" style=" margin:30px 20px;">Please type tag name:</div><div class="dia_content" style=" margin:30px 20px;"><input type="text" id="add_tag_plan" name="tags" style="width:300px; height:25px; border:solid  1px #ccc"/><div id="id_batch_add_tags_autocomplete"></div></div><div style=" margin:30px 20px;"><input type="submit" value="Submit"><input type="button" value="Cancel" onclick="this.up(2).hide();"></div></div></form>');

    // Bind the autocomplete for tags
    new Ajax.Autocompleter("add_tag_plan", "id_batch_add_tags_autocomplete",
        getURLParam().url_get_product_info, {
            minChars: 2,
            tokens: ',',
            paramName: 'name__startswith',
            method: 'get',
            // indicator: 'indicator1'
            parameters: {
                info_type: 'tags',
                format: 'ulli',
                field: 'name'
            }
        }
    );
}

function sortCase(container, plan_id, order) {   
    var parameters = $('id_form_cases').serialize(true);
    parameters.a = 'sort';

    if($F('case_sort_by') == order)
        parameters.case_sort_by = '-' + order;
    else
        parameters.case_sort_by = order;
    
    constructPlanDetailsCasesZone(container, plan_id, parameters)
}

function toggleMultiSelect(){
    $('filter_priority_selector').toggle();
    $('filter_priority_selector_multiple').toggle();
}

function changePlanCaseDefaultTester(form, container, plan_id)
{
    var p = prompt('Please type new email or username for assignee');
    if(!p)
        return false;
    
    var parameters = {
          'info_type': 'users',
          'email__startswith': p,
    }
    
    var callback = function(t) {
        var returnobj = t.responseText.evalJSON(true);
        if (returnobj.rc != 0) {
            alert(returnobj.response);
            return false;
        }
        
        constructPlanDetailsCasesZone(container, plan_id);
    }
    
    getInfoAndUpdateObject(
        parameters,
        'testcases.testcase',
        form.serialize(true)['case'],
        'default_tester_id',
        callback
    )
}
