Nitrate.TestPlans = {};
Nitrate.TestPlans.Create = {};
Nitrate.TestPlans.List = {};
Nitrate.TestPlans.Details = {};
Nitrate.TestPlans.Edit = {};
Nitrate.TestPlans.SearchCase = {};
Nitrate.TestPlans.Clone = {};

Nitrate.TestPlans.TreeView = {
	pk: new Number(),
	data: new Object(),
	tree_elements: new Element('div'),
	default_container: 'id_tree_container',
	default_parameters: {
		t: 'ajax',
	}, // FIXME: Doesn't make effect here.
	
	filter: function(parameters, callback) {
		var url = getURLParam().url_plans;
		new Ajax.Request(url, {
			method: 'get',
			parameters: parameters,
			asynchronous: false,
			onSuccess: callback,
			onFailure: json_failure,
		})
	},
	init: function(plan_id) {
		this.pk = plan_id;
		
		// Current, Parent, Brothers, Children, Temporary current
		var c_plan, p_plan, b_plans, ch_plans, tc_plan;
		
		// Get the current plan
		/*
		var p1 = { pk: plan_id, t: 'ajax'};
		var c1 = function(t) {
			var returnobj = t.responseText.evalJSON(true);
			if (returnobj.length > 0)
				c_plan = returnobj[0];
		};
		this.filter(p1, c1);
		if(!c_plan) {
			alert('Plan ' + plan_id + ' can not found in database');
			return false;
		}
		*/
		c_plan = Nitrate.TestPlans.Instance;
		
		// Get the parent plan
		if(c_plan.fields.parent) {
			var p2 = { pk: c_plan.fields.parent, t: 'ajax'};
			var c2 = function(t) {
				var returnobj = t.responseText.evalJSON(true);
				p_plan = returnobj[0];
			}
			this.filter(p2, c2);
		}
		
		// Get the brother plans
		if(c_plan.fields.parent) {
			var p3 = { parent__pk: c_plan.fields.parent, t: 'ajax'};
			var c3 = function(t) {
				var returnobj = t.responseText.evalJSON(true);
				b_plans = returnobj;
			}
			this.filter(p3, c3);
		}
		
		// Get the child plans
		var p4 = { 'parent__pk': c_plan.pk, 't': 'ajax'};
		var c4 = function(t) {
			var returnobj = t.responseText.evalJSON(true);
			ch_plans = returnobj;
		};
		this.filter(p4, c4);
		
		// Combine all of plans
		// Presume the plan have parent and brother at first
		if(p_plan && b_plans) {
			p_plan.children = b_plans;
			tc_plan = this.traverse(p_plan.children, c_plan.pk);
			tc_plan.is_current = true;
			if (ch_plans)
				tc_plan.children = ch_plans;
			
			if(p_plan.pk)
				p_plan = Nitrate.Utils.convert('obj_to_list', p_plan)
			
			this.data = p_plan;
		} else {
			c_plan.is_current = true;
			if (ch_plans)
				c_plan.children = ch_plans;
			this.data = Nitrate.Utils.convert('obj_to_list', c_plan);
		};
	},
	up: function(e) {
		var tree = Nitrate.TestPlans.TreeView;
		
		var p = {
			pk: tree.data[0].fields.parent,
			t: 'ajax'
		};
		
		var c = function(t) {
			var returnobj = t.responseText.evalJSON(true);
			var parent_obj = {0: returnobj[0], length: 1};
			parent_obj[0].children = tree.data;
			tree.data = parent_obj;
			tree.render_page();
		}
		
		tree.filter(p, c);
	},
	blind: function(e) {
		var tree = Nitrate.TestPlans.TreeView;
		var e_container = this.up();
		var e_pk = this.previous();
		var container_clns = e_container.classNames().toArray();
		
		var pk = e_pk.innerHTML;
		var obj = tree.traverse(tree.data, pk);
		
		for (i in container_clns) {
			if(typeof(container_clns[i]) != 'string')
				continue
			
			switch (container_clns[i]) {
				case 'expand':
					this.adjacent('ul')[0].hide();
					e_container.removeClassName('expand')
					e_container.addClassName('collapse');
					break;
				case 'collapse':
					if (typeof(obj.children) != 'object' || obj.children == []) {
						var c = function(t) {
							var returnobj = t.responseText.evalJSON(true);
							returnobj = Nitrate.Utils.convert('obj_to_list', returnobj);
							tree.insert(obj, returnobj);
							var ul = tree.render(returnobj);
							e_container.appendChild(ul);
						};
						
						var p = {
							parent__pk: e_pk.innerHTML,
							t: 'ajax',
						};
						tree.filter(p, c);
					};
					
					this.adjacent('ul')[0].show();
					e_container.removeClassName('collapse');
					e_container.addClassName('expand')
					break;
			}
		};
	},
	render: function(data) {
		var ul = new Element('ul');
		
		// Add the 'Up' button
		if (!data && this.data) {
			var data = this.data;
			if (data && data[0].fields.parent) {
				var li = new Element('li');
				var btn = new Element('input', {'type': 'button', 'value': 'Up'});
				li.update(btn);
				btn.observe('click', this.up);
				ul.appendChild(li);
			};
		}
		
		// Add the child plans to parent
		for (i in data) {
			if(!data[i].pk)
				continue;
			
			var li = new Element('li');
			if (data[i].extras.num_children && data[i].children)
				li.addClassName('expand');
			
			if (data[i].extras.num_children && !data[i].children)
				li.addClassName('collapse');
			
			if (data[i].is_current)
				li.addClassName('current');
			
			// Construct the items
			var title = '[<a href="' + data[i].extras.get_url_path + '">' + data[i].pk + '</a>] ';
			title += '<a class="plan_name" href="javascript:void(0);">' + data[i].fields.name + '</a>';
			title += ' (';
			if (data[i].extras.num_cases)
				title += '<a href="' + data[i].extras.get_url_path + '#testcases">' + data[i].extras.num_cases + ' cases</a>, ';
			else
				title += '0 case, ';
			
			if (data[i].extras.num_runs)
				title += '<a href="' + data[i].extras.get_url_path + '#testruns">' + data[i].extras.num_runs + ' runs</a>, ';
			else
				title += '0 runs, ';
			
			switch (data[i].extras.num_children) {
				case 0:
					title += '0 child';
					break;
				case 1:
					title += '<a href="' + data[i].extras.get_url_path + '#treeview">' + '1 child</a>';
					break;
				default:
					title += '<a href="' + data[i].extras.get_url_path + '#treeview">' + data[i].extras.num_children + ' children</a>';
					break;
			}
			
			title += ')';
			
			li.update(title);
			ul.appendChild(li);
			
			// Observe the blind link click event
			li.adjacent('a.plan_name').invoke('observe', 'click', this.blind);
			
			if(data[i].children)
				li.appendChild(this.render(data[i].children));
		};
		
		return ul;
	},
	render_page: function(container) {
		if (!container)
			container = this.default_container
		
		$(container).update(getAjaxLoading());
		$(container).update(this.render());
	},
	traverse: function(data, pk) {
		// http://stackoverflow.com/questions/3645678/javascript-get-a-reference-from-json-object-with-traverse
		for (i in data) {
			if (data[i] == [] || typeof(data[i]) != 'object')
				continue
			
			if(typeof(data[i].pk) == 'number' && data[i].pk == pk)
				return data[i];
			
			if (typeof(data[i].children) == 'object') {
				var retVal = this.traverse(data[i].children, pk);
				if (typeof(retVal) != 'undefined')
					return retVal;
			};
		};
	},
	insert: function(node, data) {
		if(node.children)
			return node;
		
		node.children = data;
		return node;
	},
};

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
    };
    
    if($('id_check_all_plans')) {
        $('id_check_all_plans').observe('click', function(e) {
            clickedSelectAll(this, $('plans_form'), 'plan_id');
        });
    }
    
    if($('testplans_table')) {
        TableKit.Sortable.init('testplans_table',
        {
            rowEvenClass : 'roweven',
            rowOddClass : 'rowodd',
            nosortClass : 'nosort'
        });
    };
    
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
        });
    };
    
    $$('input[name="plan_id"]').invoke('observe', 'click', function(t) {
        if(this.checked) {
            this.up(1).addClassName('selection_row');
        } else {
            this.up(1).removeClassName('selection_row');
        };
    });
}

Nitrate.TestPlans.Details.on_load = function()
{
    var plan_id = Nitrate.TestPlans.Instance.pk;
    // regUrl('display_summary');
    
    constructPlanDetailsCasesZone('testcases', plan_id);
    constructTagZone('tag', { plan: plan_id });
    constructPlanComponentsZone('components');
    
    TableKit.Sortable.init('testruns_table');
    TableKit.Sortable.init('testreview_table');
    
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
    
    Nitrate.TestPlans.TreeView.init(plan_id);
    Nitrate.TestPlans.TreeView.render_page();
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
    
    if($('id_table_cases')) {
        TableKit.Sortable.init('id_table_cases');
    }
    
    bindSelectAllCheckbox($('id_checkbox_all_cases'), $('id_form_cases'), 'case');
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
    
    var test = confirm("Are you sure you want to remove test case(s) from this test plan?")
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
        
        $('id_batch_component').observe('click', function(e) {
            if(this.diabled)
                return false;
                
            var params = {
                'case': $('id_form_cases').serialize(true)['case'],
                'product': Nitrate.TestPlans.Instance.product_id
            };
            
            var form_observe = function(e) {
                e.stop();
                if(!$('id_form_cases').serialize(true)['case']){
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                
                var params = this.serialize(true);
                params['case'] = $('id_form_cases').serialize(true)['case'];
                
                var url = getURLParam().url_cases_component;
                var success = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    
                    if (returnobj.rc == 0) {
                        constructPlanDetailsCasesZone(container, plan_id, parameters);
                        clearDialog();
                    } else {
                        alert(returnobj.response);
                        return false;
                    }
                }
                
                updateCaseComponent(url, params, success);
            }
            
            renderComponentForm(getDialog(), params, form_observe);
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
                    if(!returnobj.rc)
                    {
                        var html = '<div class="dia_title" style=" margin:10px 20px;">You have successfully remove <span class="red">'+ parameters.tags + '</span>&nbsp;in the following case:</div><div class="dialog_content">';
                        $('dialog').update(html);

                        returnobj.each(function(i) {
                            html += '<div class="dia_content" style=" margin:10px 20px;">'+i.pk + ' &nbsp; ' + i.fields.summary+'</div>';
                        });
                        $('dialog').update(html);
                    }

                    else
                    {
                        var html = '<div class="dia_title" style=" margin:10px 20px;"><span class="red">' + returnobj.response + '</span>';
                        $('dialog').update(html);
                    }
                    
                    
                    html +='</div><input class="dia_btn_close sprites" onclick="this.up(0).hide()" type="button" value="Close" style=" margin:10px 20px;"/>';
                    
                    $('dialog').update(html);
                    if(!returnobj.rc)
                    {
                        p = $('id_form_cases').serialize(true);
                        p.a = 'initial';
                        constructPlanDetailsCasesZone(container, plan_id, p);
                    }
                };
                var format = 'serialized';
                removeBatchTag(parameters, c, format)
             })
        
        })
        
        $('id_checkbox_all_cases').observe('click', function(e) {
            clickedSelectAll(this, this.up(4), 'case');
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
        
        $('id_checkbox_all_component').observe('click', function(e) {
            clickedSelectAll(this, this.up(4), 'component');
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
    
    var d = new Element('div');
    
    var parameters = {
        a: 'get_form',
        plan: Nitrate.TestPlans.Instance.pk,
    };
    
    var callback = function(t) {
        var action = getURLParam().url_plan_components;
        var form_observe = function(e) {
            e.stop();
            constructPlanComponentsZone('components', this.serialize());
            clearDialog();
        };
        var notice = '';
        var s = new Element('input', {'type': 'submit', 'name': 'a', 'value': 'Update'}); // Submit button
        
        var f = constructForm(d.innerHTML, action, form_observe, notice, s);
        container.update(f);
        
        // FIXME: Split the select to two columns, javascript buggy here.
        /*
        SelectFilter.init("id_component", "component", 0, "/admin_media/");
        refreshSelectFilter('component');
        */
    }
    
    // Get the form and insert into the dialog.
    constructPlanComponentsZone(d, parameters, callback);
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
                plan_id: this.plan_id,
                field: 'name',
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
    var p = prompt('Please type new email or username for default tester');
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

function constructPlanParentPreviewDialog(plan_id, parameters, callback)
{
    var action = '';
    var notice = 'This operation will overwrite existing data';
    /*
    //FIXME: Overwrite is not availabel for updateObject function yet.
    var s = new Element('span');
    var s1 = new Element('input', {type: 'checkbox', name: 'overwrite'});
    var s2 = new Element('label');
    s2.update('Overwrite exist parent.');
    var s3 = new Element('input', {type: 'submit'});
    s.appendChild(s1);
    s.appendChild(s2);
    s.appendChild(s3);
    */
    
    previewPlan(parameters, action, callback, notice);
}

function changePlanParent(container, plan_id)
{
    // container is not in using so far
    
    var tree = Nitrate.TestPlans.TreeView;
    var p = prompt('Enter new parent plan ID');
    if(!p)
        return false;
    
    if (p == plan_id) {
        alert('Nothing changed');
        return false;
    }
    
    var parameters = {
        plan_id: p,
    };
    
    var callback = function(e) {
        e.stop();
        var tree = Nitrate.TestPlans.TreeView;
        updateObject('testplans.testplan', plan_id, 'parent', this.serialize(true)['plan_id'], function(t) {
            var plan;
            var param = { plan_id: p, t: 'ajax' };
            var c = function(t) {
                plan = Nitrate.Utils.convert('obj_to_list', t.responseText.evalJSON(true));
                
                if (tree.data[0].pk == plan_id) {
                    plan[0].children = Object.clone(tree.data);
                    tree.data = plan;
                    tree.render_page();
                } else {
                    plan[0].children = Object.clone(tree.data[0].children);
                    tree.data = plan;
                    tree.render_page();
                };
                
                clearDialog();
            };
            
            tree.filter(param, c)
        });
    };
    
    constructPlanParentPreviewDialog(p, parameters, callback);
}

function addPlanChildren(container, plan_id)
{
    // container is not in using so far
    
    var tree = Nitrate.TestPlans.TreeView;
    var p = prompt('Enter a comma separated list of plan IDs');
    if(!p)
        return false;
    
    if (p == tree.data[0].pk || p == plan_id) {
        alert('Nothing changed');
        return false;
    }
    
    var parameters = {
        pk__in: p,
    };
    
    var callback = function(e) {
        e.stop();
        var tree = Nitrate.TestPlans.TreeView;
        updateObject('testplans.testplan', this.serialize(true)['plan_id'], 'parent', plan_id, function(t) {
            tree.init(plan_id);
            tree.render_page();
            clearDialog();
            alert(default_messages.alert.tree_reloaded);
        });
    };
    
    constructPlanParentPreviewDialog(p, parameters, callback);
}

function removePlanChildren(container, plan_id)
{
    // container is not in using so far
    
    var tree = Nitrate.TestPlans.TreeView;
    var p = prompt('Enter a comma separated list of plan IDs to be removed');
    if(!p)
        return false;
    
    var parameters = {
        pk__in: p,
    };
    
    var callback = function(e) {
        e.stop();
        var tree = Nitrate.TestPlans.TreeView;
        updateObject('testplans.testplan', this.serialize(true)['plan_id'], 'parent', 0, function(t) {
            tree.init(plan_id);
            tree.render_page();
            clearDialog();
            alert(default_messages.alert.tree_reloaded);
        });
    };
    
    constructPlanParentPreviewDialog(p, parameters, callback);
}
