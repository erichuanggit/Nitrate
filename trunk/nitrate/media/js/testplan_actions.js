Nitrate.TestPlans = {};
Nitrate.TestPlans.Create = {};
Nitrate.TestPlans.List = {};
Nitrate.TestPlans.Advance_Search_List = {};
Nitrate.TestPlans.Details = {};
Nitrate.TestPlans.Edit = {};
Nitrate.TestPlans.SearchCase = {};
Nitrate.TestPlans.Clone = {};
Nitrate.TestPlans.Attachment = {};

/*
 * Hold container IDs
 */
Nitrate.TestPlans.CasesContainer = {
    // containing cases with confirmed status
    ConfirmedCases: 'testcases',
    // containing cases with non-confirmed status
    ReviewingCases: 'reviewcases'
};

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
        var parent_obj, brother_obj; 

        var parent_param = {
            pk: tree.data[0].fields.parent,
            t: 'ajax'
        };
        
        var parent_callback = function(t) {
            var returnobj = t.responseText.evalJSON(true);
            parent_obj = {0: returnobj[0], length: 1};
        }; 
        tree.filter(parent_param, parent_callback);

        var brother_param = {
            parent__pk: tree.data[0].fields.parent,
            t: 'ajax'
        };

        var brother_callback = function(t){
            var returnobj = t.responseText.evalJSON(true);
            brother_obj = returnobj;
        };

        tree.filter(brother_param, brother_callback);

        if (parent_obj && brother_obj.length) {
            parent_obj[0].children = brother_obj;
            var brother_numbers = brother_obj.length;
            for (i = 0; i < brother_numbers; i++) {
                if (parent_obj[0].children[i].pk == tree.data[0].pk) {
                   parent_obj[0].children[i] = tree.data[0];
                   break;
                }
            }
            tree.data = parent_obj;
            tree.render_page();
        }
    },
    blind: function(e) {
        var tree = Nitrate.TestPlans.TreeView;
        var e_container = this;
        var li_container = e_container.up(1);
        var e_pk = e_container.next('a').innerHTML;
        var container_clns = e_container.classNames().toArray();
        var expand_icon_url = '/media/images/t2.gif';
        var collapse_icon_url = '/media/images/t1.gif';
        var obj = tree.traverse(tree.data, e_pk);
        
        for (i in container_clns) {
            if(typeof(container_clns[i]) != 'string')
                continue
            
            switch (container_clns[i]) {
                case 'expand_icon':
                    li_container.down('ul').hide();
                    e_container.src = collapse_icon_url;
                    e_container.removeClassName('expand_icon');
                    e_container.addClassName('collapse_icon');
                    break;
                case 'collapse_icon':
                    if (typeof(obj.children) != 'object' || obj.children == []) {
                        var c = function(t) {
                            var returnobj = t.responseText.evalJSON(true);
                            returnobj = Nitrate.Utils.convert('obj_to_list', returnobj);
                            tree.insert(obj, returnobj);
                            var ul = tree.render(returnobj);
                            li_container.appendChild(ul);
                        };
                        
                        var p = {
                            parent__pk: e_pk,
                            t: 'ajax',
                        };
                        tree.filter(p, c);
                    };
                    
                    li_container.down('ul').show();
                    e_container.src = expand_icon_url;
                    e_container.removeClassName('collapse_icon');
                    e_container.addClassName('expand_icon');
                    break;
            }
        };
    },
    render: function(data) {
        var ul = new Element('ul');
        var icon_expand = '<img src="/media/images/t2.gif" class="expand_icon">';
        var icon_collapse = '<img src="/media/images/t1.gif" class="collapse_icon">';
        
        // Add the 'Up' button
        if (!data && this.data) {
            var data = this.data;
            if (data && data[0].fields.parent) {
                var li = new Element('li');
                var btn = new Element('input', {'type': 'button', 'value': 'Up'});
                li.update(btn);
                btn.observe('click', this.up);
                li.addClassName('no-list-style');
                ul.appendChild(li);
            };
        }
        
        // Add the child plans to parent
        for (i in data) {
            if(!data[i].pk)
                continue;
            
            var li = new Element('li');
            var title = '[<a href="' + data[i].extras.get_url_path + '">' + data[i].pk + '</a>] ';

            if (data[i].extras.num_children && data[i].children){
                title = icon_expand + title;
                li.addClassName('no-list-style');
            }
            
            if (data[i].extras.num_children && !data[i].children){
                title = icon_collapse + title;
                li.addClassName('no-list-style');
            }
            
            if (data[i].is_current)
                li.addClassName('current');
            
            if (data[i].fields.is_active)
                title = '<div>' + title;
            else
                title = '<div class="line-through">' + title;

            // Construct the items
            title += '<a class="plan_name" href="' + data[i].extras.get_url_path + '">' + data[i].fields.name + '</a>';
            title += ' (';
            if (data[i].extras.num_cases && data[i].is_current)
                title += '<a href="#testcases" onclick="FocusTabOnPlanPage(this)">' + data[i].extras.num_cases + ' cases</a>, ';
            else if (data[i].extras.num_cases && !(data[i].is_current))
                title += '<a href="' + data[i].extras.get_url_path + '#testcases">' + data[i].extras.num_cases + ' cases</a>, ';
            else
                title += '0 case, ';
            
            if (data[i].extras.num_runs && data[i].is_current)
                title += '<a href="#testruns" onclick="FocusTabOnPlanPage(this)">' + data[i].extras.num_runs + ' runs</a>, ';
            else if (data[i].extras.num_runs && !data[i].is_current)
                title += '<a href="' + data[i].extras.get_url_path + '#testruns">' + data[i].extras.num_runs + ' runs</a>, ';
            else
                title += '0 runs, ';

            if (data[i].is_current){
                switch (data[i].extras.num_children) {
                    case 0:
                        title += '0 child';
                        break;
                    case 1:
                        title += '<a href="#treeview" onclick="expandCurrentPlan(this.up(0))">' + '1 child</a>';
                        break;
                    default:
                        title += '<a href="#treeview" onclick="expandCurrentPlan(this.up(0))">' + data[i].extras.num_children + ' children</a>';
                        break;
                }
            }else{
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

            }
            
            title += ')</div>';
            
            li.update(title);
            ul.appendChild(li);
            
            // Observe the blind link click event
            li.adjacent('img').invoke('observe', 'click', this.blind);
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

Nitrate.TestPlans.Advance_Search_List.on_load = function()
{
    if($('id_product')) {
        bind_version_selector_to_product(true);
    };
    
    if($('id_check_all_plans')) {
        $('id_check_all_plans').observe('click', function(e) {
            clickedSelectAll(this, $('plans_form'), 'plan');
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

Nitrate.TestPlans.List.on_load = function()
{
    if($('id_product')) {
        bind_version_selector_to_product(true);
    };
    
    if($('id_check_all_plans')) {
        $('id_check_all_plans').observe('click', function(e) {
            clickedSelectAll(this, $('plans_form'), 'plan');
        });
    };
//     
    // if($('testplans_table')) {
        // TableKit.Sortable.init('testplans_table',
        // {
            // rowEvenClass : 'roweven',
            // rowOddClass : 'rowodd',
            // nosortClass : 'nosort'
        // });
    // };
    
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

    var oTable;
    oTable = jQ('#testplans_table').dataTable({
        "iDisplayLength": 20,
        "sPaginationType": "full_numbers",
        "bFilter": false,
        // "bLengthChange": false,
        "aLengthMenu": [[10, 20, 50, -1], [10, 20, 50, "All"]],
        "aaSorting": [[ 1, "desc" ]],
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": "/plans/ajax/"+this.window.location.search,
        "aoColumns": [
          {"bSortable": false },
          null,
          {"sType": "html"},
          {"sType": "html"},
          {"sType": "html"},
          null,
          {"bVisible": false},
          null,
          {"bSortable": false },
          {"bSortable": false },
          {"bSortable": false }
        ]
        });
}

Nitrate.TestPlans.Details = {

    /*
     * Lazy-loading TestPlans TreeView
     */
    loadPlansTreeView: function(plan_id) {
        // TableKit.Sortable.init('testreview_table');
        // Initial the tree view
        Nitrate.TestPlans.TreeView.init(plan_id);
        Nitrate.TestPlans.TreeView.render_page();
    },

    initTabs: function() {
        $$('li.tab a').invoke('observe', 'click', function(i) {
            $$('div.tab_list').each(function(t) {
                t.hide();
            });

            $$('li.tab').each(function(t) {
                t.removeClassName('tab_focus');
            });
            this.parentNode.addClassName('tab_focus');
            var tab_array = this.href.toArray();
            var tab = '';
            for (var i = tab_array.indexOf('#') + 1; i < tab_array.length; i++)
                tab += tab_array[i]
            $(tab).show();
        });

        // Display the tab indicated by hash along with URL.
        var defaultSwitchTo = '#testcases';
        var switchTo = window.location.hash;
        var exist = jQ('#contentTab')
            .find('a')
            .map(function(index, element) {
                return element.getAttribute('href');
            })
            .filter(function(index, element) {
                return element === switchTo;
            }).length > 0;
        if (!exist) {
            switchTo = defaultSwitchTo;
        }
        fireEvent($$('a[href=\"' + switchTo + '\"]')[0], 'click');
    },

    /*
     * Load cases table.
     *
     * Proxy of global function with same name.
     */
    loadCases: function(container, plan_id, parameters) {
        constructPlanDetailsCasesZone(container, plan_id, parameters);

        if (Nitrate.TestPlans.Details._bindEventsOnLoadedCases === undefined) {
            Nitrate.TestPlans.Details._bindEventsOnLoadedCases = bindEventsOnLoadedCases({
                cases_container: container,
                plan_id: plan_id,
                parameters: parameters
            });
        }
    },

    /*
     * Loading newly created cases with proposal status to show table of these
     * kind of cases.
     */
    loadConfirmedCases: function(plan_id) {
        var params = {
            'a': 'initial',
            'template_type': 'case',
            'from_plan': plan_id
        };
        var container = Nitrate.TestPlans.CasesContainer.ConfirmedCases;
        Nitrate.TestPlans.Details.loadCases(container, plan_id, params);
    },

    /*
     * Loading reviewing cases to show table of these kind of cases.
     */
    loadReviewingCases: function(plan_id) {
        var params = {
            'a': 'initial',
            'template_type': 'review_case',
            'from_plan': plan_id
        };
        var container = Nitrate.TestPlans.CasesContainer.ReviewingCases;
        Nitrate.TestPlans.Details.loadCases(container, plan_id, params);
    },

    bindEventsOnLoadedCases: function(container) {
        var elem = $(container);
        var form = elem.childElements()[0];
        var table = elem.childElements()[1];
        Nitrate.TestPlans.Details._bindEventsOnLoadedCases(table, form);
    },

    /*
     * Show the remaining number of TestCases to be loaded.
     *
     * A side-effect is that when there is no more TestCases to be loaded,
     * disable Show More hyperlink and display descriptive text to tell user
     * what is happening.
     */
    showRemainingCasesCount: function(container) {
        var contentContainer = jQ('#' + container);
        var casesListContainer = contentContainer.find('.js-cases-list');
        var totalCasesCount = contentContainer
			.find('.js-remaining-cases-count').attr('data-cases-count');
        var loadedCasesCount = casesListContainer.find('tr[id]').length;
        var remainingCount = parseInt(totalCasesCount) - parseInt(loadedCasesCount);
        contentContainer.find('.js-number-of-loaded-cases').text(loadedCasesCount);
        if (remainingCount === 0) {
            contentContainer.find('a.js-load-more').die('click').toggle();
            contentContainer.find('span.js-loading-progress').toggle();
            contentContainer.find('span.js-nomore-msg').toggle();
            setTimeout(function() {
                contentContainer.find('span.js-nomore-msg').toggle('slow');
            }, 2000);
        } else {
            contentContainer.find('.js-remaining-cases-count').text(remainingCount);
        }
    },

    /*
     * The real function to load more cases and show them in specific container.
     */
    loadMoreCasesClicHandler: function(e, container) {
        var elemLoadMore = jQ('#' + container).find('.js-load-more');
        var post_data = elemLoadMore.attr('data-criterias');
        var page_index = elemLoadMore.attr('data-page-index');
        var page_index_re = /page_index=\d+/;
        if (post_data.match(page_index_re))
          post_data = post_data.replace(page_index_re, 'page_index=' + page_index);
        else
          post_data = post_data + '&page_index=' + page_index;

        jQ('#' + container).find('.ajax_loading').show();

        jQ.post('/cases/load-more/',
            post_data,
            function(data) {
                var has_more = jQ(data)[0].hasAttribute('id');
                if (has_more) {
                    jQ('#' + container).find('.ajax_loading').hide();

                    var casesListContainer = jQ('#' + container).find('.js-cases-list');
                    casesListContainer.find('tbody:first').append(data);

                    // Increase page index for next batch cases to load
                    var page_index = elemLoadMore.attr('data-page-index');
                    elemLoadMore.attr('data-page-index', parseInt(page_index) + 1);

                    Nitrate.TestPlans.Details.bindEventsOnLoadedCases(container);

                    // Calculate the remaining number of cases
                    Nitrate.TestPlans.Details.showRemainingCasesCount(container);
                } else {
                    elemLoadMore.unbind('click').remove();
                }
            }).fail(function() {
                jQ('#' + container).find('.ajax_loading').hide();
                alert('Cannot load subsequent cases.');
            });
    },

    /*
     * Load more cases with previous criterias.
     */
    onLoadMoreCasesClick: function(e) {
        var container = Nitrate.TestPlans.CasesContainer.ConfirmedCases;
        Nitrate.TestPlans.Details.loadMoreCasesClicHandler(e, container);
    },

    /*
     * Load more reviewing cases with previous criterias.
     */
    onLoadMoreReviewcasesClick: function(e) {
        var container = Nitrate.TestPlans.CasesContainer.ReviewingCases;
        Nitrate.TestPlans.Details.loadMoreCasesClicHandler(e, container);
    },

    observeLoadMore: function(container) {
        var NTC = Nitrate.TestPlans.CasesContainer;
        var NTD = Nitrate.TestPlans.Details;
        var loadMoreEventHandlers = {};
        loadMoreEventHandlers[NTC.ConfirmedCases] = NTD.onLoadMoreCasesClick;
        loadMoreEventHandlers[NTC.ReviewingCases] = NTD.onLoadMoreReviewcasesClick;
        var eventHandler = loadMoreEventHandlers[container];
        if (eventHandler) {
            jQ('#' + container).find('.js-load-more')
                .die('click')
                .live('click', eventHandler);
        }
    },

    observeEvents: function(plan_id) {
        var NTPD = Nitrate.TestPlans.Details;

        $('tab_testcases').observe('click', function(e) {
            if (!NTPD.testcasesTabOpened) {
                NTPD.loadConfirmedCases(plan_id);
                NTPD.testcasesTabOpened = true;
            };
        });

        $('tab_treeview').observe('click', function(e) {
            if (!NTPD.plansTreeViewOpened) {
                NTPD.loadPlansTreeView(plan_id);
                NTPD.plansTreeViewOpened = true;
            }
        });

        $('tab_reviewcases').observe('click', function(e) {
            var opened  = Nitrate.TestPlans.Details.reviewingCasesTabOpened;
            if (!opened) {
                Nitrate.TestPlans.Details.loadReviewingCases(plan_id);
                Nitrate.TestPlans.Details.reviewingCasesTabOpened = true;
            }
        });

        // Initial the enable/disble btns
        if($('btn_disable')) {
            $('btn_disable').observe('click', function(e){
                updateObject('testplans.testplan', plan_id, 'is_active', 'False', 'bool', reloadWindow);
            });
        }

        if($('btn_enable')) {
            $('btn_enable').observe('click', function(e) {
                updateObject('testplans.testplan', plan_id, 'is_active', 'True', 'bool', reloadWindow);
            });
        }
    },

    on_load: function() {
        var plan_id = Nitrate.TestPlans.Instance.pk;
        // regUrl('display_summary');
        //

        // Initial the contents
        constructTagZone('tag', { plan: plan_id });
        constructPlanComponentsZone('components');

        Nitrate.TestPlans.Details.observeEvents(plan_id);
        Nitrate.TestPlans.Details.initTabs();

        TableKit.Sortable.init('testruns_table');

        // Make the import case dialog draggable.
        new Draggable('id_import_case_zone');

        // Bind for run form
        $('id_form_run').observe('submit', function(e) {
            if(!this.serialize(true)['run']) {
                e.stop();
                alert(default_messages.alert.no_run_selected);
            }
        });

        $('id_check_all_runs').observe('click', function(e) {
            clickedSelectAll(this, 'testruns_table', 'run');
        });

        Nitrate.Utils.enableShiftSelectOnCheckbox('case_selector');
        Nitrate.Utils.enableShiftSelectOnCheckbox('run_selector');

        Nitrate.TestPlans.Runs.initializaRunTab();
        Nitrate.TestPlans.Runs.bind();
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
    // Populate product version field.
    if($('id_product') && !$F('id_default_product_version')){
        fireEvent($('id_product'),'change');
    }
}

Nitrate.TestPlans.Attachment.on_load = function()
{
    jQ(document).ready(function() {
       jQ("#upload_file").change(function ()
       {
         var iSize = jQ("#upload_file")[0].files[0].size;
         var limit = parseInt(jQ('#upload_file').attr('limit'));

         if (iSize > limit)
         {
             alert("Your attachment's size is beyond limit, please limit your attachments to under 5 megabytes (MB).");
         }
      });
    });
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
    debug_output('Successd to hook with the upload plan summary button');

    new Ajax_upload($('id_btn_upload_plan_summary'), {
        action: '/plan/new/uploadsummary/',
        name: 'plan_summary',

        onSubmit: function(file, extension) {
            debug_output('Upload plan document success submit');
            
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

/*
 * Deprecated function. Remove it when it's confirmed that not being referenced by others any more.
 */
function unlinkCasePlan(container, parameters) 
{
    parameters.a = 'delete_cases';
    
    if(!parameters['case']) {
        alert('At least one case is required to delete.');
        return false;
    }
    
    var c = confirm("Are you sure you want to delete test case(s) from this test plan?");
    if (!c)
        return false;
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        if(returnobj.rc == 0) {
            parameters.a = 'initial';
            constructPlanDetailsCasesZone(container, parameters.from_plan, parameters);
            return true;
        }
        
        alert(returnobj.response);
    }
    
    var url = new String('cases/');
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: success,
        onFailure: json_failure
    })
}

/*
 * Unlink selected cases from current TestPlan.
 *
 * Rewrite function unlinkCasePlan to avoid conflict. Remove it when confirm it's not used any more.
 */
function unlinkCasesFromPlan(container, form, table)
{
    var selection = serializeCaseFromInputList2(table);
    if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
        alert('At least one case is required to delete.');
        return false;
    }

    var parameters = serialzeCaseForm(form, table, true);
    parameters.a = 'delete_cases';
    if (selection.selectAll) {
        parameters.selectAll = selection.selectAll;
    }
    parameters.case = selection.selectedCasesIds;

    var c = confirm("Are you sure you want to delete test case(s) from this test plan?");
    if (!c) {
        return false;
    }

    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        if(returnobj.rc == 0) {
            parameters.a = 'initial';
            constructPlanDetailsCasesZone(container, parameters.from_plan, parameters);
            return true;
        }
        alert(returnobj.response);
    }

    var url = new String('cases/');
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: success,
        onFailure: json_failure
    })
}

function refreshCasesSelectionCheck(container) {
    var casesMostCloseContainer = jQ(container).find('.js-cases-list');
    var notSelectAll = casesMostCloseContainer.find('input[name="case"]:not(:checked)').length > 0;
    casesMostCloseContainer.find('input[value="all"]')[0].checked = !notSelectAll;

    // Toggle select all option
    jQ(container).find('.js-cases-select-all').find('input[type="checkbox"]')[0].checked = !notSelectAll;
    if (notSelectAll) {
        jQ(container).find('.js-cases-select-all').hide('fast');
    } else {
        jQ(container).find('.js-cases-select-all').show('fast');
    }
}

/*
 * When check the All box, to show or hide Select All option to user.
 */
function toggleSelectAllInput(container, selectAll) {
    var selectAllDiv = jQ(container).find('.js-cases-select-all');
    selectAllDiv.find('input[type="checkbox"]')[0].checked = selectAll;
    if (selectAll) {
        selectAllDiv.show('fast');
    } else {
        selectAllDiv.hide('fast');
    }
}

/*
 * Bind events on loaded cases.
 *
 * This is a closure. The real function needs cases container, plan's ID, and
 * initial parameters as the initializatio parameters.
 *
 * Arguments:
 * - container: the HTML element containing all loaded cases. Currently, the
 *   container is a TABLE.
 */
function bindEventsOnLoadedCases(options) {
    var parameters = options.parameters;
    var plan_id = options.plan_id;
    var cases_container = options.cases_container;

    return function(container, form) {
        jQ(cases_container).find('.js-cases-list')
                           .find('input[name="case"]')
                           .live('click', function(e) {
            refreshCasesSelectionCheck(cases_container);
        });

        // Observe the change sortkey
        container.adjacent('.case_sortkey.js-just-loaded').invoke('observe', 'click', function(e) {
            var c = this.next(); // Container
            var params = {
                'testcaseplan': c.innerHTML,
                'sortkey': this.innerHTML,
            };
            var callback = function(t) {
                constructPlanDetailsCasesZone(cases_container, plan_id, parameters);
            };
            changeCaseOrder(params, callback)
        });

        container.adjacent('.change_status_selector.js-just-loaded').invoke('observe', 'change', function(e) {
            var be_confirmed = (this.value == '2');
            var was_confirmed = (this.up(0).attributes['status'].value == "CONFIRMED");
            var case_id = this.up(1).id;
            changeTestCaseStatus(plan_id, this, case_id, be_confirmed, was_confirmed);
        });

        // Display/Hide the case content
        container.adjacent('.expandable.js-just-loaded').invoke('observe', 'click', function(e) {
            var btn = this;
            var title = this.up(); // Container
            var content = this.up().next(); // Content Containers
            var case_id = title.id;
            var template_type = form.adjacent('input[name="template_type"]')[0].value;
            // Review case content call back;
            var review_case_content_callback = function(e) {
                var comment_container_t = new Element('div');
                // Change status/comment callback
                var cc_callback = function(e) {
                    e.stop();
                    var params = this.serialize(true);
                    var refresh_case = function(t) {
                        var td = new Element('td', {colspan: 12});
                        var id = 'id_loading_' + params['object_pk'];
                        td.appendChild(getAjaxLoading(id));
                        content.update(td);
                        fireEvent(btn, 'click');
                        fireEvent(btn, 'click');
                    }
                    submitComment(comment_container_t, params, refresh_case);
                };
                content.adjacent('.update_form').invoke('stopObserving', 'submit');
                content.adjacent('.update_form').invoke('observe', 'submit', cc_callback);

                // Observe the delete comment form
                var rc_callback = function(e) {
                    e.stop();
                    if(!confirm(default_messages.confirm.remove_comment))
                        return false;
                    var params = this.serialize(true);
                    var refresh_case = function(t) {
                        var returnobj = t.responseText.evalJSON();
                        if (returnobj.rc != 0) {
                            alert(returnobj.response);
                            return false;
                        }

                        var td = new Element('td', {colspan: 12});
                        var id = 'id_loading_' + params['object_pk'];
                        td.appendChild(getAjaxLoading(id));
                        content.update(td);
                        fireEvent(btn, 'click');
                        fireEvent(btn, 'click');
                    }
                    removeComment(this, refresh_case)
                };
                content.adjacent('.form_comment').invoke('stopObserving', 'submit');
                content.adjacent('.form_comment').invoke('observe', 'submit', rc_callback);
            };

            switch(template_type) {
            case 'review_case':
                var case_content_callback = review_case_content_callback;
                break;
            default:
                var case_content_callback = function(e) {};
            }

            toggleTestCaseContents(template_type, title, content, case_id, nil, nil, case_content_callback);
        });

        /*
         * Using class just-loaded to identify thoes cases that are just loaded to
         * avoid register event handler repeatedly.
         */
        var elems = container.adjacent('.js-just-loaded');
        elems.each(function(elem) {
            elem.removeClassName('js-just-loaded');
        });
    }
}


/*
 * Serialize form data including the selected cases for AJAX requst.
 *
 * Used in function `constructPlanDetailsCasesZone'.
 */
function serializeFormData(options) {
    var form = options.form;
    var container = options.zoneContainer;
    var selection = options.casesSelection;
    var hashable = options.hashable || false;

    var formdata = form.serialize(hashable);

    // some dirty data remains in the previous criteria, remove them.
    // FIXME: however, this is not a good way. CONSIDER to reuse filter form.
    var prevCriterias = jQ(container).find('.js-load-more')
                                     .attr('data-criterias')
                                     .replace(/a=\w+/, '')
                                     .replace(/&?selectAll=1/, '')
                                     .replace(/&?case=\d+/g, '');
    var unhashableData = prevCriterias;
    if (selection.selectAll) {
        unhashableData += '&selectAll=1';
    }
    var casepks = [''];
    var loopCount = selection.selectedCasesIds.length;
    var selectedCasesIds = selection.selectedCasesIds;
    for (var i = 0; i < loopCount; i++) {
        casepks.push('case=' + selectedCasesIds[i]);
    }
    unhashableData += casepks.join('&');

    if (hashable) {
        var arr = unhashableData.split('&');
        for (var i = 0; i < arr.length; i++) {
            var parts = arr[i].split('=');
            var key = parts[0], value = parts[1];
            // FIXME: not sure how key can be an empty string
            if (key.length === 0) {
                continue;
            }
            if (key in formdata) {
                // Before setting value, the original value must be converted to an array object.
                if (formdata[key].push === undefined) {
                    formdata[key] = [formdata[key], value];
                } else {
                    formdata[key].push(value);
                }
            } else {
                formdata[key] = value;
            }
        }
    } else {
        formdata += '&' + unhashableData;
    }

    return formdata;
}

function constructPlanDetailsCasesZone(container, plan_id, parameters)
{
    if (typeof(container) != 'object')
        container = $(container)
    
    container.update('<div class="ajax_loading"></div>');
    
    if(!parameters)
        var parameters = {'a': 'initial', 'from_plan': plan_id}

    var _bindEventsOnLoadedCases = bindEventsOnLoadedCases({
        cases_container: container,
        plan_id: plan_id,
        parameters: parameters
    });
    
    complete = function(t) {
        var form = container.childElements()[0];
        var table = container.childElements()[2];
        
        // Presume the first form element is the form
        if (!form.tagName == 'FORM') {
            alert('form element of container is not a form');
            return false;
        };

        var filter = form.adjacent('.list_filter')[0];

        // Filter cases
        form.observe('submit', function(e) {
            e.stop();
            var params = serializeCaseForm2(form, table, true, true);
            constructPlanDetailsCasesZone(container, plan_id, params);
        });

        // Change the case backgroud after selected
        form.adjacent('input[name="case"]').invoke('observe', 'click', function(e) {
            if(this.checked) {
                this.up(1).addClassName('selection_row');
            } else {
                this.up(1).removeClassName('selection_row');
            }
        });

        // Observe the check all selectbox
        if (form.adjacent('input[value="all"]').length > 0) {
            var element = form.adjacent('input[value="all"]')[0];

            element.observe('click', function(e) {
                clickedSelectAll(this, this.up(4), 'case');
            });
        }

        if(form.adjacent('.btn_filter').length > 0) {
            var element = form.adjacent('.btn_filter')[0];
            element.observe('click', function(t) {
                if(filter.getStyle('display') == 'none'){
                    filter.show();
                    this.update(default_messages.link.hide_filter);
                } else {
                    filter.hide();
                    this.update(default_messages.link.show_filter);
                }
            });
        }

        // Bind click the tags in tags list to tags field in filter
        if(form.adjacent('.taglist a[href="#testcases"]').length > 0) {
            var elements = form.adjacent('.taglist a');
            elements.invoke('observe', 'click', function(e) {
                if(filter.style.display == 'none')
                    fireEvent(form.adjacent('.filtercase')[0], 'click');
                /*if(form.tag__name__in.value){
                    form.tag__name__in.value = form.tag__name__in.value + ',' + this.innerHTML;
                }else{
                    form.tag__name__in.value = this.innerHTML;
                }*/
                form.tag__name__in.value = form.tag__name__in.value?(form.tag__name__in.value + ',' + this.textContent):this.textContent;
            });
        }

        // Bind the sort link
        if(form.adjacent('.btn_sort').length > 0) {
            var element = form.adjacent('.btn_sort')[0];
            element.observe('click', function(e) {
                var params = serialzeCaseForm(form, table);
                var callback = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    if(returnobj.rc != 0) {
                        alert(returnobj.reponse);
                    }
                    params.a = 'initial';
                    constructPlanDetailsCasesZone(container, plan_id, params);
                }
                resortCasesDragAndDrop(container, this, form, table, params, callback);
            });
        }

        // Bind batch change case status selector
        if(form.adjacent('input[name="new_case_status_id"]').length > 0) {
            var element = form.adjacent('input[name="new_case_status_id"]')[0];
            
            element.observe('change',function(t) {
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                var status_pk = this.value;
                if (!status_pk) {
                    return false;
                }
                var c = confirm(default_messages.confirm.change_case_status);
                if (!c) {
                    return false;
                }

                var postdata = serializeFormData({
                    form: form,
                    zoneContainer: container,
                    casesSelection: selection,
                    hashable: true
                });
                postdata.a = 'update';
                postdata.target_field = 'case_status';
                postdata.new_value = status_pk;

                var callback = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    
                    if(returnobj.rc == 0) {
                        constructPlanDetailsCasesZone(container, plan_id, postdata);
                        jQ('#run_case_count').text(returnobj.run_case_count);
                        jQ('#case_count').text(returnobj.case_count);
                        jQ('#review_case_count').text(returnobj.review_case_count);
                    } else {
                        alert(returnobj.response);
                        return false;
                    }
                }

                new Ajax.Request('/ajax/update/cases-case-status/', {
                    method: 'post',
                    parameters: postdata,
                    onSuccess: callback,
                    onFailure: json_failure
                });
            });
        }

        if(form.adjacent('input[name="new_priority_id"]').length > 0) {
            var element = form.adjacent('input[name="new_priority_id"]')[0];
            element.observe('change', function(t) {
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                // FIXME: how about show a message to user to let user know what is happening?
                if(!this.value) {
                    return false;
                }
                var c = confirm(default_messages.confirm.change_case_priority);
                if (!c) {
                    return false;
                }

                var postdata = serializeFormData({
                    form: form,
                    zoneContainer: container,
                    casesSelection: selection,
                    hashable: true
                });
                postdata.a = 'update';
                postdata.target_field = 'priority';
                postdata.new_value = this.value;

                var callback = function(t) {
                    returnobj = t.responseText.evalJSON(true);
                    if(returnobj.rc != 0) {
                        alert(returnobj.response);
                        return false
                    };
                    constructPlanDetailsCasesZone(container, plan_id, postdata);
                };

                new Ajax.Request('/ajax/update/cases-priority/', {
                    method: 'post',
                    parameters: postdata,
                    onSuccess: callback,
                    onFailure: json_failure
                });
            })
        }

        // Observe the batch case automated status button
        if (form.adjacent('input.btn_automated').length > 0) {
            var element = form.adjacent('input.btn_automated')[0];
            element.observe('click', function(e) {
                var selection = serializeCaseFromInputList2(table);
                var noCasesSelected = !selection.selectAll && selection.selectedCasesIds.length === 0;
                if(noCasesSelected) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }

                var dialogContainer = getDialog();
                var callback = function(t) {
                    returnobj = t.responseText.evalJSON(true);

                    if(returnobj.rc != 0) {
                        alert(returnobj.response);
                        return false
                    };

                    var params = serialzeCaseForm(form, table, true, true);
                    /*
                     * FIXME: this is confuse. There is no need to assign this
                     *        value explicitly when update component and category.
                     */
                    params.a = 'search';
                    params.case = selection.selectedCasesIds;
                    constructPlanDetailsCasesZone(container, plan_id, params);
                    clearDialog(dialogContainer);
                };

                constructCaseAutomatedForm(dialogContainer, callback, {
                    zoneContainer: container,
                    casesSelection: selection
                });
            })
        }

        if(form.adjacent('input.btn_component').length > 0) {
            var element = form.adjacent('input.btn_component')[0];
            element.observe('click', function(e) {
                if(this.diabled)
                    return false;
                var c = getDialog();
                var params = {
                    // FIXME: remove this line. It's unnecessary any more.
                    'case': serializeCaseFromInputList(table),
                    'product': Nitrate.TestPlans.Instance.fields.product_id
                };
                if(params['case'] && params['case'].length == 0){
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                var form_observe = function(e) {
                    e.stop();

                    var selection = serializeCaseFromInputList2(table);
                    var noCasesSelected = !selection.selectAll && selection.selectedCasesIds.length === 0;
                    if(noCasesSelected) {
                        alert(default_messages.alert.no_case_selected);
                        return false;
                    }

                    var params = serializeFormData({
                        form: this,
                        zoneContainer: container,
                        casesSelection: selection
                    });

                    var url = getURLParam().url_cases_component;
                    var callback = function(t) {
                        returnobj = t.responseText.evalJSON(true);

                        if (returnobj.rc != 0) {
                            alert(returnobj.response);
                            return false;
                        }
                        parameters['case'] = selection.selectedCasesIds;
                        constructPlanDetailsCasesZone(container, plan_id, parameters);
                        clearDialog(c);
                    }

                    updateCaseComponent(url, params, callback);
                }
                renderComponentForm(c, params, form_observe);
            })
        };
        
        if(form.adjacent('input.btn_category').length > 0) {
            var element = form.adjacent('input.btn_category')[0];
            element.observe('click', function(e) {
                if(this.diabled)
                    return false;
                var c = getDialog();
                var params = {
                    /*
                     * FIXME: the first time execute this code, it's unnecessary
                     *        to pass selected cases' ids to the server.
                     */
                    'case': serializeCaseFromInputList(table),
                    'product': Nitrate.TestPlans.Instance.fields.product_id
                };
                if(params['case'] && params['case'].length == 0){
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                var form_observe = function(e) {
                    e.stop();

                    var selection = serializeCaseFromInputList2(table);
                    var noCasesSelected = !selection.selectAll && selection.selectedCasesIds.length === 0;
                    if(noCasesSelected) {
                        alert(default_messages.alert.no_case_selected);
                        return false;
                    }

                    var params = serializeFormData({
                        form: this,
                        zoneContainer: container,
                        casesSelection: selection
                    });

                    var url = getURLParam().url_cases_category;
                    var callback = function(t) {
                        returnobj = t.responseText.evalJSON(true);

                        if (returnobj.rc != 0) {
                            alert(returnobj.response);
                            return false;
                        }

                        parameters['case'] = selection.selectedCasesIds;
                        constructPlanDetailsCasesZone(container, plan_id, parameters);
                        clearDialog(c);
                    }

                    updateCaseCategory(url, params, callback);
                }
                renderCategoryForm(c, params, form_observe);
            })
        };

        if(form.adjacent('input.btn_default_tester').length != 0) {
            var element = form.adjacent('input.btn_default_tester')[0];
            element.observe('click', function(e) {
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }

                var params = serializeFormData({
                    form: form,
                    zoneContainer: container,
                    casesSelection: selection,
                    hashable: true
                });
                params.a = 'update';

                var callback = function(t) {
                    var returnobj = t.responseText.evalJSON();
                    
                    if (returnobj.rc != 0) {
                        alert(returnobj.response);
                        return false
                    };
                    constructPlanDetailsCasesZone(container, plan_id, params);
                };

                changeCaseMember(params, callback);
            })
        }

        if (form.adjacent('input.sort_list').length != 0) {
            var element = form.adjacent('input.sort_list')[0];
            element.observe('click', function(e) {
                // NOTE: new implemenation does not use testcaseplan.pk
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                var postdata = serializeFormData({
                    form: form,
                    zoneContainer: container,
                    casesSelection: selection,
                    hashable: true
                });

                var callback = function(t) {
                    postdata.case = selection.selectedCasesIds;
                    constructPlanDetailsCasesZone(container, plan_id, postdata);
                };
                changeCaseOrder2(postdata, callback);
            });
        }

        if(form.adjacent('input.btn_reviewer').length > 0) {
            var element = form.adjacent('input.btn_reviewer')[0];
            element.observe('click', function(e) {
                var case_pks = serializeCaseFromInputList(table);
                
                if(case_pks.length == 0){
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                
                var callback = function(t) {
                    var returnobj = t.responseText.evalJSON();
                    
                    if (returnobj.rc != 0) {
                        alert(returnobj.response);
                        return false
                    };
                    
                    constructPlanDetailsCasesZone(container, plan_id, parameters);
                }
                
                var field = 'reviewer';
                changeCaseMember(table, field, case_pks, callback);
            })
        }

        // Tag call back
        // Callback for display the cases that just added tags
        var tag_callback = function(t) {
            var dialog = getDialog();
            
            returnobj = t.responseText.evalJSON(true);
            if (returnobj.rc && returnobj.rc == 1) {
                alert(returnobj.response);
                clearDialog(dialog);
                return false;
            };
            
            clearDialog(dialog);
            dialog.show();
            var html = '<div class="dia_title" style=" margin:10px 20px;">You have successfully operate tags in the following case:</div><div class="dialog_content">';
            dialog.update(html);
            
            returnobj.each(function(i) {
                html += '<div class="dia_content" style=" margin:10px 20px;">'+i.pk + ' &nbsp; ' + i.fields.summary+'</div>';
            });
            dialog.update(html);
            
            html +='</div><input class="dia_btn_close sprites" onclick="this.up(0).hide()" type="button" value="Close" style=" margin:10px 20px;"/>';
            
            dialog.update(html);
            params = serialzeCaseForm(form, table);
            params.a = 'initial';
            constructPlanDetailsCasesZone(container, plan_id, params);
        };
        
        // Observe the batch add case button
        if (form.adjacent('input.tag_add').length > 0) {
            var element = form.adjacent('input.tag_add')[0];
            element.observe('click',function(e) {
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }

                constructBatchTagProcessDialog(plan_id);

                // Observe the batch tag form submit
                $('id_batch_tag_form').observe('submit', function(e){
                    e.stop();

                    var tagData = this.serialize(true);
                    if(!tagData.tags) {
                        return false;
                    }
                    var params = serializeFormData({
                        form: form,
                        zoneContainer: container,
                        casesSelection: selection,
                        hashable: true
                    });
                    params.tags = tagData.tags;

                    /*
                     * Two reasons to force to remove plan from parameters here.
                     * 1. plan is added in previous cases filter. As the design
                     *    of Show More, previous filter criteria is added for
                     *    selecting all cases with same filter criteria.
                     * 2. existing plan confuses tag view method due to it
                     *    applies to both plan and case to add tag. Thus, the
                     *    existing plan will cause it to add tag to all cases of
                     *    that plan always.
                     *
                     * Placing this line of code is not a good idea. But, it
                     * works well for the current implementation. Possible
                     * solution to avoid this might to split the tag view method
                     * to add tags to plans and cases, respectively. Why to make
                     * change to tag view method? That is, according to the
                     * cases filter implementation, plan must exist in the
                     * filter criteria as a parameter.
                     */
                    delete params.plan;

                    var format = 'serialized';
                    addBatchTag(params, tag_callback, format);
                });
            });
        }
        
        // Observe the batch remove tag function
        if(form.adjacent('input.tag_delete').length > 0) {
            var element = form.adjacent('input.tag_delete')[0];
            element.observe('click',function(e) {
                var c = getDialog();
                var selection = serializeCaseFromInputList2(table);
                if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
                    alert(default_messages.alert.no_case_selected);
                    return false;
                }
                var form_observe = function(e) {
                    e.stop();

                    var params = serializeFormData({
                        form: this,
                        zoneContainer: container,
                        casesSelection: selection,
                    });

                    var url = getURLParam().url_cases_tag;
                    var callback = function(t) {
                        returnobj = t.responseText.evalJSON(true);

                        if (returnobj.rc != 0) {
                            alert(returnobj.response);
                            return false;
                        }
                        parameters['case'] = selection.selectedCasesIds;
                        constructPlanDetailsCasesZone(container, plan_id, parameters);
                        clearDialog(c);
                    }

                    updateCaseTag(url, params, callback);
                }
                renderTagForm(c, {case: selection.selectedCasesIds}, form_observe);

                // FIXME: seems this piece of code never gets called. Remove it after confirmation.
                // Observe the batch tag form submit
                $('id_batch_tag_form').observe('submit',function(e) {
                    e.stop();
                    var params = this.serialize(true);
                    params['case'] = serializeCaseFromInputList(table);
                    if(!params.tags)
                        return false;
                    
                    // Callback for display the cases that just added tags
                    var format = 'serialized';
                    removeBatchTag(params, tag_callback, format)
                 })
            })
            }

        jQ(container).find('input[value="all"]').live('click', function(e) {
            toggleSelectAllInput(container, this.checked);
        });

        _bindEventsOnLoadedCases(table, form);

        // Register event handler for loading more cases.
        Nitrate.TestPlans.Details.observeLoadMore(container.id);
        Nitrate.TestPlans.Details.showRemainingCasesCount(container.id);

        refreshCasesSelectionCheck(container);
    };

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
            var c = confirm(default_messages.confirm.remove_case_component);
            if(!c)
                return false;
            var links = $$('.link_remove_plan_component');
            var index = links.indexOf(this);
            var component = $$('input[type="checkbox"][name="component"]')[index];
            
            var p = $('id_form_plan_components').serialize(true);
            p['component'] = component.value;
            p['a'] = 'remove';
            constructPlanComponentsZone(container, p, callback);
        })
        
        $('id_checkbox_all_component').observe('click', function(e) {
            clickedSelectAll(this, this.up(4), 'component');
        });

        var c_count = jQ('tbody#component').attr('count');
        jQ('#component_count').text(c_count);
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
        var notice = 'Press "Ctrl" to select multiple default component';
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

function constructBatchTagProcessDialog(plan_id){
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
                testcase__plan__pk: plan_id,
                field: 'name',
            }
        }
    );
}

function sortCase(container, plan_id, order) {
    var form = container.childElements()[0];
    var parameters = form.serialize(true);
    parameters.a = 'sort';
    
    if(parameters.case_sort_by == order)
        parameters.case_sort_by = '-' + order;
    else
        parameters.case_sort_by = order;
    constructPlanDetailsCasesZone(container, plan_id, parameters)
}

function toggleMultiSelect(){
    $('filter_priority_selector').toggle();
    $('filter_priority_selector_multiple').toggle();
}

function changeCaseMember(parameters, callback)
{
    var p = prompt('Please type new email or username');
    if(!p) {
        return false;
    }

    parameters.target_field = 'default_tester';
    parameters.new_value = p;

    new Ajax.Request('/ajax/update/cases-default-tester/', {
        method: 'post',
        parameters: parameters,
        onSuccess: callback,
        onFailure: json_failure
    })   
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
        var c = function(t) {
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
        };
        updateObject('testplans.testplan', plan_id, 'parent', this.serialize(true)['plan_id'], 'int', c);
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
        var c = function(t) {
            tree.init(plan_id);
            tree.render_page();
            clearDialog();
            alert(default_messages.alert.tree_reloaded);
        };
        
        updateObject('testplans.testplan', this.serialize(true)['plan_id'], 'parent', plan_id, 'int', c);
    };
    
    constructPlanParentPreviewDialog(p, parameters, callback);
}

function removePlanChildren(container, plan_id)
{
    // container is not in using so far
    
    var tree = Nitrate.TestPlans.TreeView;
    var plan_obj = tree.traverse(tree.data, plan_id);
    var children_pks = new Array();
    for (var i = 0; i < plan_obj.children.length; i++)
        children_pks.push(plan_obj.children[i].pk);
    var p = prompt('Enter a comma separated list of plan IDs to be removed');
    if(!p)
        return false;
    var prompt_pks = p.split(',');
    for(var j = 0 ; j < prompt_pks.length; j++){
        if (prompt_pks[j].include(plan_id)){
            alert('can not remove current plan');
            return false;
        }
        else if (!children_pks.include(prompt_pks[j])){
            alert('plan ' + prompt_pks[j] + ' is not the child node of current plan');
            return false;
        }
        else
            continue;
    }
    var parameters = {
        pk__in: p,
    };
    
    var callback = function(e) {
        e.stop();
        var tree = Nitrate.TestPlans.TreeView;
        var c = function(t) {
            tree.init(plan_id);
            tree.render_page();
            clearDialog();
            alert(default_messages.alert.tree_reloaded);
        };
        updateObject('testplans.testplan', this.serialize(true)['plan_id'], 'parent', 0, 'None', c);
    };
    
    constructPlanParentPreviewDialog(p, parameters, callback);
}

function resortCasesDragAndDrop(container, button, form, table, parameters, callback)
{
    if (button.innerHTML != 'Done Sorting') {
        // Remove the elements affact the page
        form.adjacent('.blind_all_link').invoke('remove'); // Remove blind all link
        form.adjacent('.case_content').invoke('remove');
        form.adjacent('.blind_icon').invoke('remove');
        form.adjacent('.show_change_status_link').invoke('remove');
        table.adjacent('.expandable').invoke('stopObserving');
        
        // Use the selector content to replace the selector
        form.adjacent('.change_status_selector').each(function(t) {
            var w = t.selectedIndex;
            t.replace((new Element('span')).update(t.options[w].text));
        });
        
        /*
        // Use the title to replace the blind down title link
        form.adjacent('.blind_title_link').each(function(t) {
            t.replace((new Element('span')).update(t.innerHTML));
        });
        
        // Use the sortkey content to replace change sort key link
        form.adjacent('.mark').each(function(t) {
            t.update(t.down().innerHTML);
        });
        */
        
        // init the tableDnD object
        new TableDnD().init(table);
        button.innerHTML = 'Done Sorting';
        table.adjacent('tr').invoke('addClassName', 'cursor_move');
    } else {
        // $('id_sort_control').hide();
        button.replace((new Element('span')).update('...Submitting changes'));
        
        table.adjacent('input[type=checkbox]').each(function(t) {
            t.checked = true;
            t.disabled = false;
        });
        
        parameters.a = 'order_cases';
        parameters.case_sort_by = 'sortkey'; 
        var url = new String('cases/');
        new Ajax.Request(url, {
            method: 'post',
            parameters: parameters,
            onSuccess: callback,
            onFailure: json_failure
        })
    }
}

function FocusTabOnPlanPage(element){
    var tab_array = element.href.toArray();
    var tab_name = '';
    for (var i = tab_array.indexOf('#') + 1; i < tab_array.length; i++)
        tab_name += tab_array[i]
    $('tab_treeview').removeClassName('tab_focus');
    $('treeview').hide();
    $('tab_' + tab_name).addClassName('tab_focus');
    $(tab_name).show();
}

function expandCurrentPlan(element){
    var tree = Nitrate.TestPlans.TreeView;
    if (element.getElementsByClassName('collapse_icon').length > 0){
        var e_container = element.getElementsByClassName('collapse_icon')[0];
        var li_container = e_container.up(1);
        var e_pk = e_container.next('a').innerHTML;
        var expand_icon_url = '/media/images/t2.gif';
        var obj = tree.traverse(tree.data, e_pk);
        if (typeof(obj.children) != 'object' || obj.children == []) {
            var c = function(t) {
                var returnobj = t.responseText.evalJSON(true);
                returnobj = Nitrate.Utils.convert('obj_to_list', returnobj);
                tree.insert(obj, returnobj);
                var ul = tree.render(returnobj);
                li_container.appendChild(ul);
            };
            
            var p = {
                parent__pk: e_pk,
                t: 'ajax',
            };
            tree.filter(p, c);
        }
        li_container.down('ul').show();
        e_container.src = expand_icon_url;
        e_container.removeClassName('collapse_icon');
        e_container.addClassName('expand_icon');
    }
}

Nitrate.TestPlans.Runs = {

    bind: function () {
        /**
         * Bind everything.
         *
        **/
        var that = this;
        jQ('#show_more_runs').live('click', that.showMore);
        jQ('#reload_runs').live('click', that.reload);
        jQ('#tab_testruns').live('click', that.initializaRunTab);
        jQ('.btn-statistics').live('click', that.percent);
        jQ('#btn_selected_progress').live('click', that.showPercentageOfSelectedRuns);
        jQ('.run_selector').live('change', that.reactsToRunSelection);
        jQ('#id_check_all_runs').live('change', that.reactsToAllRunSelectorChange);
    }

    , makeUrlFromPlanId: function (planId) {
        return '/plan/' + planId + '/runs/';
    }

    , makePercentUrlFromRunId: function (runId) {
        return '/run/' + runId + '/percent/';
    }

    , render: function (data, textStatus, jqXHR) {
        var tbody = jQ('#testruns_body');
        var html = jQ(data.html);
        var btnCheckAll = jQ('#box_select_rest input:checkbox');
        if (btnCheckAll.length > 0 && btnCheckAll.is(':checked')) {
            html.find('.run_selector').attr('checked', 'checked');
        };
        tbody.append(html);
    }

    , initializaRunTab: function () {
        /**
         * Load the first page of the runs when:
         * 1. Current active tab is #testrun;
         * AND
         * 2. No testruns are ever loaded.
         *
        */
        var that = Nitrate.TestPlans.Runs;
        if (jQ('#tab_testruns').hasClass('tab_focus')) {
            var tbody = jQ('#testruns_body');
            if (tbody.children().length === 0) {
                that.reload();
            }
        }
    }

    , showLoading: function () {
        var loader = jQ('#img_loading_runs');
        loader.show();
    }

    , hideLoading: function () {
        var loader = jQ('#img_loading_runs');
        loader.hide();
    }

    , reactsToRunSelection: function () {
        var that = Nitrate.TestPlans.Runs;
        var selection = jQ('.run_selector:not(:checked)')
        var controller = jQ('#id_check_all_runs');
        if (selection.length == 0) {
            controller.attr('checked', true);
        } else {
            controller.attr('checked', false);
        }
        controller.trigger('change');
    }

    , reactsToAllRunSelectorChange: function (event) {
        var that = Nitrate.TestPlans.Runs;
        if (jQ(event.target).attr('checked')) {
            that.toggleRemainingRunSelection('on');
        } else {
            that.toggleRemainingRunSelection('off');
        }
    }

    , toggleRemainingRunSelection: function (status) {
         var area = jQ('#box_select_rest');
         if (area.length > 0) {
            if (status === 'off') {
            area.find('input:checkbox').attr('checked', false);
            area.hide();
             } else {
                area.find('input:checkbox').attr('checked', true);
                area.show();
             }
         };
    }

    , nextPage: function (planId) {
        var that = this;
        var url = that.makeUrlFromPlanId(planId);
        var request = jQ.ajax({
            dataType: 'json',
            url: url,
            data: that.filter(),
            beforeSend: that.showLoading
        }).done(that.render);
        return request;
    }

    , filter: function (data) {
        var queryString = jQ("#run_filter").serialize();
        // store this string into the rest result select box
        var box = jQ('#box_select_rest');
        box.find('input:checkbox').val(queryString);
        return queryString;
    }

    , showMore: function () {
        var that = Nitrate.TestPlans.Runs;
        var showMoreLink = jQ('#show_more_runs');
        if (showMoreLink.attr('ended') === 'yes') {
            return false;
        }
        var planId = showMoreLink.attr('plan');
        var localPageNum = parseInt(jQ('[name=page_num]').val());
        var request = that.nextPage(planId);
        request.done(function(data, textStatus, jqXHR) {
            // Update the local page number
            if (localPageNum < data.numPages) {
                var remaining = (data.numPages - localPageNum);
                localPageNum++;
                jQ('[name=page_num]').val(localPageNum);
                showMoreLink.html("Show More (" + remaining + " pages left)");
            } else {
                showMoreLink.html("End");
                showMoreLink.attr('ended', 'yes');
            }
        });
        request.done(that.hideLoading);
        return false;
    }

    , reload: function () {
        var that = Nitrate.TestPlans.Runs;
        // clean the table
        var tbody = jQ('#testruns_body');
        tbody.empty();
        var page = jQ('[name=page_num]');
        page.val('1');
        var showMoreLink = jQ('#show_more_runs');
        showMoreLink.html('Show More');
        showMoreLink.attr('ended', 'no');
        that.showMore();
        return false;
    }

    , percent: function (clicked) {
        var that = Nitrate.TestPlans.Runs;
        var target = jQ(clicked.target);
        var runId = target.attr('run');
        var url = that.makePercentUrlFromRunId(runId)
        var status = target.attr('status');
        var request = jQ.ajax(url, {
            dataType: 'json',
            data: {'status': status},
            beforeSend: function () {
                target.text('calculating ...');
            }
        });
        request.done(function (data, textStatus, jqXHR) {
           // display the result
           var percentage = data['percent'];
           // locate the <tr> with runID
           var tr = jQ('#run_' + runId);
           // update the percentage with status name
           var bar = tr.find('.'+status).find('.progress-bar');
           var slots = bar.children();
           jQ(slots[0]).text(percentage + '%');
           jQ(slots[1]).css({'width': percentage+'px'});
           target.hide(); // hide the button link
           bar.show(); // show the progress bar
        });
        return false;
    }

    , showPercentageOfSelectedRuns: function () {
        var checkedBoxes = jQ('.run_selector:checked');
        checkedBoxes.each(function (index, box) {
            jQ(box).parent().parent().find('.btn-statistics').each(function (index, elem) {
                var clickable = jQ(elem);
                if (clickable.css('display') != 'none') {
                    clickable.trigger('click');
                }
            });
        });
    }
}

/*
 * Request specific operation upon filtered TestCases.
 *
 * Default HTTP method is GET.
 *
 * Options:
 * - url: the URL representing the service requesting to now.
 * - form: containing all necessary data serialized as the data included in REQUEST.
 * - casesContainer: containing all INPUT with type checkbox, each of them holds every filtered
 *                   TestCase' Id. Typcicall, it's a TABLE in the current implementation.
 *
 * FIXME: this function is similar to some other functions within tcms_actions.js, that wraps
 *        function postToURL. All these functions have almost same behavior. Abstraction can be done
 *        better.
 */
function requestOperationUponFilteredCases(options) {
    var requestMethod = options.requestMethod || 'get';
    var url = options.url;
    var form = options.form;
    var casesContainer = options.table;

    var selection = serializeCaseFromInputList2(casesContainer);
    if (!selection.selectAll && selection.selectedCasesIds.length === 0) {
        alert('At least one case is required by a run.');
        return false;
    }
    // Exclude selected cases, that will be added from the selection.
    var params = serializeCaseForm2(form, casesContainer, true, true);
    if (selection.selectAll) {
        params.selectAll = selection.selectAll;
    }
    params.case = selection.selectedCasesIds;
    postToURL(url, params, requestMethod);
}

/*
 * Write new run from partial or all filtered cases.
 */
function writeNewRunFromFilteredCases(options) {
    return requestOperationUponFilteredCases(options);
}

/*
 * Add partial or all filtered cases to an existing TestRun.
 */
function addFilteredCasesToRun(options) {
    return requestOperationUponFilteredCases(options);
}

/*
 * Request clone current selected TestCases
 */
function requestCloneFilteredCases(options) {
    return requestOperationUponFilteredCases(options);
}
