// Create a dictionary to avoid polluting the global namespace:
var Nitrate = {};
Nitrate.Utils = {};
var short_string_length = 100;

/*
    Utility function.
    Set up a function callback for after the page has loaded
 */
Nitrate.Utils.after_page_load = function(callback) {
    Event.observe(window, 'load', callback);
};

Event.observe(window, 'load', function(e) {
    var dropDownMenu = Class.create();
    
    dropDownMenu.prototype = {
        initialize: function(cls){
            this.cls = cls;
            this.init();
        },  
        
        init: function(){
            $$(this.cls).each(function(o){
                o.observe("mouseover", function(i) {
                    if(o.down(1))
                        o.down(1).show();
                });
                
                o.observe("mouseout", function(i) {
                    if(o.down(1))
                        o.down(1).hide();
                });
            });
        }
    };
    
    var newnewMenu = new dropDownMenu(".nav_li");  
});

var default_messages = {
    'alert': {
        'no_case_selected': 'No cases selected! Please select at least one case.',
        'ajax_failure': 'Commnucation with server got some unknown errors.'
    },
    'confirm': {
        'change_case_status': 'Are you sure to change the status?',
        'change_case_priority': 'Are you sure to change the priority?',
        'remove_case_component': 'Are you sure you wish to delete these component(s)?\nThe action will unable to undo.'
    },
    'link': {
        'hide_filter': 'Hide filter options',
        'show_filter': 'Show filter options',
    },
    'report': {
        'hide_search':'Hide the coverage search',
        'show_search':'Show the coverage search'
    }
}

function getURLParam()
{
    args = $A(arguments);
    id = args[0];
    
    var param = new Object();
    
    param.url_login = '/accounts/login/';
    param.url_logout = '/accounts/logout/';
    
    param.url_get_product_info = '/management/getinfo/';
    param.url_get_form = '/ajax/form/';
    param.url_upload_file = '/management/uploadfile/';

    param.url_search_users = '/management/accounts/search/';
    param.url_change_user_group = '/management/account/' + id + '/changegroup/';
    param.url_change_user_status = '/management/account/' + id + '/changestatus/';

    param.url_plan_components  = '/plans/component/';
    param.url_modify_plan  = '/plan/' + id + '/modify/';
    param.url_plan_assign_case = '/plan/' + id + '/assigncase/apply/';
    
    param.url_change_case_run_status = '/run/' + id + '/execute/changestatus/';
    param.url_change_case_run_order = '/run/' + id + '/changecaserunorder/';
    
    param.url_search_case = '/cases/';
    param.url_create_case = '/case/create/';
    param.url_cases_automated = '/cases/automated/';
    param.url_cases_component = '/cases/component/';
    param.url_modify_case = '/case/' + id + '/modify/';
    param.url_case_change_status = '/cases/changestatus/';
    param.url_change_case_order = '/case/' + id + '/changecaseorder/';
    
    param.url_runs_env_value = '/runs/env_value/'

    param.url_manage_env_categories = '/management/environments/categories/';
    param.url_manage_env_properties = '/management/environments/properties/';
    param.url_manage_env_property_values = '/management/environments/propertyvalues/';

    return param;
}


// Exceptions for Ajax
var json_failure = function(t)
{
    returnobj = t.responseText.evalJSON(true);
    if(returnobj.response)
        alert(returnobj.response);
    else
        alert(returnobj);
    return false;
}

var html_failure = function()
{
    alert(default_messages.alert.ajax_failure);
    return false;
}

var json_success_refresh_page = function(t)
{
    returnobj = t.responseText.evalJSON(true);
    
    if (returnobj.rc == 0) {
        window.location.reload();
    } else {
        alert(returnobj.response);
        return false;
    }
}

function setCookie(name, value, expires, path, domain, secure) { 
    var curCookie = name + "=" + escape(value) + 
        ((expires) ? "; expires=" + expires.toGMTString() : "") + 
        ((path) ? "; path=" + path : "") + 
        ((domain) ? "; domain=" + domain : "") + 
        ((secure) ? "; secure" : ""); 
    document.cookie = curCookie; 
}

function checkCookie()
{
    var exp = new Date(); 
    exp.setTime(exp.getTime() + 1800000); 
    // first write a test cookie 
    setCookie("cookies", "cookies", exp, false, false, false); 
    if (document.cookie.indexOf('cookies') != -1) { 
        // alert("Got Cookies!");
        // now delete the test cookie 
        exp = new Date(); 
        exp.setTime(exp.getTime() - 1800000); 
        setCookie("cookies", "cookies", exp, false, false, false);

        return true;
    } else { 
        // alert("No Cookies!"); 
        return false;
    } 
}

function removeItem(item)
{
    $(item).remove();
}

function splitString(str, num)
{
    cut_for_dot = num - 3;
    
    if(str.length > num)
        return str.substring(0, cut_for_dot) + "...";
        
    return str;
}

/* 
    Set up the <option> children of the given <select> element.
    Preserving the existing selection (if any).

    @element: a <select> element
    @values: a list of (id, name) pairs
    @allow_blank: boolean.  If true, prepend a "blank" option
*/
function set_up_choices(element, values, allow_blank)
{
    var innerHTML = "";
    var selected_ids = new Array();
    
    if(!element.multiple) {
        // Process the single select box
        selected_ids.push(element.value);
    } else {
        // Process the select box with multiple attribute
        for (var i = 0; (node = element.options[i]); i++) {
           if(node.selected)
               selected_ids.push(node.value)
        }
    }
    
    // Set up blank option, if there is one:
    if (allow_blank) {
        innerHTML += '<option value="">---------</option>';
    }
    
    // Add an <option> for each value:
    values.each( function(item) {
        var item_id = item[0];
        var item_name = item[1];
        var optionHTML = '<option value="' + item_id + '"';
        
        var display_item_name = item_name
        var cut_for_short = false;
        if(item_name.length > short_string_length) {
            display_item_name = splitString(item_name, short_string_length);
            var cut_for_short = true;
        }
        
        selected_ids.each(function(i) {
            if(i == item_id)
                optionHTML += ' selected="selected"';
        })
        
        if(cut_for_short) {
            optionHTML += ' title="' + item_name + '"';
        }
        
        optionHTML += '>' + display_item_name + '</option>';
        innerHTML += optionHTML;
    });
    
    // Copy it up to the element in the DOM:
    element.innerHTML = innerHTML;
}

function getBuildsByProductId(allow_blank, product_field, build_field, is_active)
{
    if(!product_field)
        var product_field = new String('id_product')
    
    if(!build_field) {
        if($('id_build')) {
            var build_field = new String('id_build');
        } else {
            alert('Build field is not exist');
            return false;
        }
    }
    
    var product_id = $F(product_field);
    var is_active = '';
    if($('value_sub_module')) {
        if($F('value_sub_module') == "new_run")
            is_active = true;
    }
    
    if(is_active) {
        is_active = true;
    }
    
    if(product_id == "")
    {
        $(build_field).innerHTML = '<option value="">---------</option>';
        return false;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        debug_output('Get builds succeed get ready to replace the select widget inner html');
        
        set_up_choices($(build_field), 
                       returnobj.collect(function(o) {
                           return [o.pk, o.fields.name];
                       }),
                       allow_blank);
        
        debug_output('Update builds completed');
        
        if($F('value_sub_module') == "new_run")
            if($(build_field).innerHTML == '')
                alert('You should create new build first before create new run');
    }
    
    var failure = function(t) {
        alert("Update builds and envs failed");
    }
    
    var url = getURLParam().url_get_product_info;
    new Ajax.Request(url, {
        method: 'get',
        parameters: {
            info_type: 'builds',
            product_id: product_id,
            is_active: is_active,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure
    });
}

function getEnvsByProductId(allow_blank, product_field)
{
    if(!product_field)
        var product_field = new String('id_product')
    
    product_id = $F(product_field);
    var args = false;
    if($('value_sub_module')) {
        if($F('value_sub_module') == "new_run")
            args = 'is_active'
    }
    
    if(product_id == "")
    {
        $('id_env_id').innerHTML = '<option value="">---------</option>';
        return true;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        try {
            console.log('Get environments succeed get ready to replace the select widget inner html');
        } catch(err) {}
        
        set_up_choices($('id_env_id'), 
                       returnobj.collect(function(o) {
                           return [o.pk, o.fields.name];
                       }),
                       allow_blank);

        if(document.title == "Create new test run")
            if($('id_env_id').innerHTML == '')
                alert('You should create new enviroment first before create new run');
    }

    var failure = function(t) {
        alert("Update builds and envs failed");
    }

    
    var url = getURLParam().url_get_product_info;
    new Ajax.Request(url, {
        method:'get',
        parameters:{
            info_type: 'envs',
            product_id: product_id,
            args: args,
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: success, 
        onFailure: failure});
}


function getVersionsByProductId(allow_blank, product_field, version_field)
{
    if(!product_field)
        var product_field = new String('id_product')
    
    if(!version_field) {
        if($('id_product_version')) {
            var version_field = new String('id_product_version');
        } else if ($('id_default_product_version')) {
            var version_field = new String('id_default_product_version');
        } else {
            alert('Version field is not exist');
            return false;
        }
    }
    
    product_id = $F(product_field);
    
    if(product_id == "" && allow_blank)
    {
        $(version_field).innerHTML = '<option value="">---------</option>';
        return true;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        try {
            console.log('Get versions succeed get ready to replace the select widget inner html');
        } catch(err) {}

        set_up_choices($(version_field), 
                       returnobj.collect(function(o) {
                           return [o.pk, o.fields.value];
                       }),
                       allow_blank);
    }

    var failure = function(t) {
        alert("Update versions failed");
    }

    
    var url = getURLParam().url_get_product_info;
    new Ajax.Request(url,
                     {method:'get',
                      parameters:{info_type:'versions',
                                  product_id:product_id},
                      requestHeaders: {Accept: 'application/json'},
                      onSuccess:success, 
                      onFailure:failure});
}

function getPropertiesByProductId(allow_blank, container)
{
    product_id = $F('id_product_id');
    var url = getURLParam().url_get_product_info;
    new Ajax.Updater(container, url, { parameters: {
            info_type: 'properties',
            product_id: product_id,
        }, 
        method: 'get', 
        insertion: Insertion.Bottom
    })
}

function getComponentsByProductId(allow_blank, product_field, component_field, callback, parameters)
{
    if(!parameters)
        var parameters = {};
    
    parameters.info_type = 'components';
    
    // Initial the product get from
    if (!parameters || !parameters.product_id) {
        if(!product_field)
            var product_field = new String('id_product')
        product_id = $F(product_field);
        parameters.product_id = product_id
    }
    
    if(!component_field) {
        if($('id_component')) {
            var component_field = new String('id_component');
        } else {
            alert('Component field is not exist');
            return false;
        }
    }
    
    if(parameters.product_id == "")
    {
        $(component_field).innerHTML = '<option value="">---------</option>';
        return true;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        set_up_choices($(component_field), 
                       returnobj.collect(function(o) {
                           return [o.pk, o.fields.name];
                       }),
                       allow_blank);
        
        if (callback) {
            callback.call();
        }
    }
    
    var failure = function(t) {
        alert("Update components failed");
    }
    
    var url = getURLParam().url_get_product_info;
    
    new Ajax.Request(url,{
        method:'get',
        parameters: parameters,
        requestHeaders: {Accept: 'application/json'},
        onSuccess:success, 
        onFailure:failure
    });
}

function getCategorisByProductId(allow_blank, product_field, category_field)
{   
    if(!product_field)
        var product_field = new String('id_product')
    
    product_id = $F(product_field);
    
    if(!category_field) {
        if($('id_category')) {
            var category_field = new String('id_category');
        } else {
            alert('Category field is not exist');
            return false;
        }
    }
    
    debug_output('Get categories from product ' + product_id);
        
    if(product_id == "")
    {
        $(category_field).innerHTML = '<option value="">---------</option>';
        return true;
    }
    
    var success = function(t) {
        returnobj = t.responseText.evalJSON(true);
        
        set_up_choices(
            $(category_field), returnobj.collect(function(o) {
                return [o.pk, o.fields.name];
            }), allow_blank
        );
        
        debug_output('Get categories succeed get ready to replace the select widget inner html');
    }

    var failure = function(t) {
        alert("Update category failed");
    }

    
    var url = getURLParam().url_get_product_info;
    new Ajax.Request(url, {method:'get',
                           parameters:{info_type:'categories',
                                       product_id:product_id},
                           requestHeaders: {Accept: 'application/json'},
                           onSuccess:success, 
                           onFailure:failure});
}

function checkProductField(product_field)
{
    if(product_field)
        return product_field
    
    if($('id_product'))
        return $('id_product')
    
    alert('No product field');
    return false;
}

function bind_build_selector_to_product(allow_blank, product_field, build_field, active)
{
    var product_field = checkProductField(product_field)
    
    if(product_field) {
        product_field.observe('change', getBuildsByProductId.curry(
            allow_blank, product_field, build_field, active
        ));
        
        getBuildsByProductId(allow_blank, product_field, build_field, active);
    }
}

function bind_env_selector_to_product(allow_blank)
{
    $('id_product_id').observe('change', 
                               getEnvsByProductId.curry(allow_blank));
    getEnvsByProductId(allow_blank);
}

function bind_version_selector_to_product(allow_blank, load, product_field, version_field)
{
    var product_field = checkProductField(product_field)
    
    if(product_field) {
        product_field.observe('change', getVersionsByProductId.curry(
            allow_blank, product_field, version_field
        ))
        if (load)
            getVersionsByProductId(allow_blank, product_field, version_field);
    };
}

function bind_category_selector_to_product(allow_blank, load, product_field, category_field)
{
    var product_field = checkProductField(product_field)
    
    if(product_field) {
        product_field.observe('change', getCategorisByProductId.curry(
            allow_blank, product_field, category_field
        ));
        if (load)
            getCategorisByProductId(allow_blank);
    }
}

function bind_component_selector_to_product(allow_blank, load, product_field, component_field)
{
    var product_field = checkProductField(product_field)
    
    if(product_field) {
        $(product_field).observe('change', getComponentsByProductId.curry(
            allow_blank, product_field, component_field
        ));
        
        if (load)
            getComponentsByProductId(allow_blank);
    }
}

function bind_properties_selector_to_product(allow_blank, container)
{
    var product_field = checkProductField(product_field)
    
    if(product_field) {
        product_field.observe('change', function(t) { 
            $(container).innerHTML = "";
            getPropertiesByProductId(allow_blank, container);               
        });
        getPropertiesByProductId(allow_blank, container);
    }
}

function FORM(props, kids)
{
    return Builder.node('form', props, kids);
}

function TR(props, kids)
{
    return Builder.node('tr', props, kids);
}

function TD(props, kids)
{
    return Builder.node('td', props, kids);
}

function INPUT(props, kids)
{
    return Builder.node('input', props, kids);
}

function A(props, kids)
{
    return Builder.node('a', props, kids);
}

function SPAN(props)
{
    return Builder.node('a', props);
}

// debug_output function is implement with firebug plugin for firefox

function debug_output(value)
{
    try {
        console.log(value);
    } catch(err) {}
}

function dragdrop(element) {
    new Draggable(element);
}

function myCustomURLConverter(url, node, on_save) {
    return url;
}


function regUrl(container){
    var str=$(container).innerHTML;
    var reg=/(http:\/\/)?(www\.)(\w+\.)+\w+/ig;
    var reg1=/(http:\/\/)/ig;
    var pre;
    if(result=str.match(reg))
        {
            for(i=0;i<result.length;i++)
            {
                if(result[i].match(reg1))
                pre='';
                else
                pre='http://';
                str1="<a href='"+pre+result[i]+"'>"+result[i]+"</a>";
                str=str.replace(result[i],str1);
            }
        }
    $(document).innerHTML=str;
}

// Stolen from http://www.webdeveloper.com/forum/showthread.php?t=161317

function fireEvent(obj,evt){
    var fireOnThis = obj;
    if( document.createEvent ) {
        var evObj = document.createEvent('MouseEvents');
        evObj.initEvent( evt, true, false );
        fireOnThis.dispatchEvent(evObj);
    } else if( document.createEventObject ) {
        fireOnThis.fireEvent('on'+evt);
    }
}

// Stolen from http://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit

function postToURL(path, params, method) {
    method = method || "post"; // Set method to post by default, if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        var hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", params[key]);

        form.appendChild(hiddenField);
    }

    document.body.appendChild(form);    // Not entirely sure if this is necessary
    form.submit();
}

function constructTagZone(container, parameters)
{
    $(container).update('<div class="ajax_loading"></div>');
    
    var complete = function(t) {
        new Ajax.Autocompleter("id_tags", "id_tags_autocomplete", getURLParam().url_get_product_info, {
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
        });
        
        $('id_tag_form').observe('submit', function(i){
            i.stop();
            
            constructTagZone(container, this.serialize(true));
            
            // this.adjacent('input[name="tags"]').invoke('focus');
        })
    }
    
    var url = new String('/management/tags/');
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
}

function addTag(container)
{
    constructTagZone(container, $('id_tag_form').serialize(true));
}

function removeTag(container, tag)
{
    $('id_tag_form').adjacent('input[name="handle"]')[0].value = 'remove';
    
    parameters = $('id_tag_form').serialize(true);
    parameters.tags = tag;
    
    constructTagZone(container, parameters);
}
function editTag(container, tag)
{
	newtag = prompt('Please type your new tag', tag);
	parameters = $('id_tag_form').serialize(true);
	parameters.tags = newtag;
    var complete = function(t) {
        removeTag(container,tag)
    }
   var url = new String('/management/tags/');
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
    
}


function addBatchTag(parameters, callback, format)
{
    parameters.handle = 'add';
    parameters.type = 'json';
    parameters.format = format;
    batchProcessTag(parameters, callback, format);
    
}

function removeBatchTag(parameters, callback, format)
{
    parameters.handle = 'remove';
    parameters.type = 'json';
    parameters.format = format;
    batchProcessTag(parameters, callback, format);
}


function batchProcessTag(parameters, callback, format)
{
    var success = function(t) {
        if(!format) {
            returnobj = t.responseText.evalJSON(true);
            
            if (returnobj.response == 'ok') {
                if(callback)
                    callback.call();
            } else {
                alert(returnobj.response);
                return false;
            }
        } else {
            callback(t);
        }
    }
    
    var url = new String('/management/tags/')
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: success,
    })
}

function bindCommentDeleteLink(container, parameters)
{
    // Bind delete link
    var d_success = function(t) {
        constructCommentZone(container, parameters);
    }
    
    var d_objects = container.adjacent('.commentdelete');
    
    d_objects.invoke('stopObserving');
    d_objects.invoke('observe', 'click', function(i) {
        if(!confirm('Are you sure to delete the comment?'))
            return false;
        var d_form = this.up();
        
        new Ajax.Request(d_form.action, {
            method: d_form.method,
            parameters: d_form.serialize(),
            onSuccess: d_success,
        })
    })
}

function constructCommentZone(container, parameters)
{
    var complete = function(t) {
        bindCommentDeleteLink(container, parameters);
    }
    
    $(container).update('<div class="ajax_loading"></div>');
    
    var url = new String('/comments/list/');
    
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
        onComplete: complete,
    })
}

function submitComment(container, parameters)
{
    var complete = function(t) {
        bindCommentDeleteLink(container, parameters);
    }
    
    $(container).update('<div class="ajax_loading"></div>');
    
    var url = new String('/comments/post/')
    
    new Ajax.Updater(container, url, {
        method: 'post',
        parameters: parameters,
        onComplete: complete,
    })
}

function previewPlan(container, parameters){
    if (!parameters.plan_id) {
        alert('Plan is required');
        return false;
    }
    
    /*
    if(!isInteger(parameters.plan_id)) {
        alert('Plan ID must be a number');
        return false;
    }
    */
    
    var url = new String('/plan/' + parameters.plan_id + '/');
    
    new Ajax.Updater(container, url, {
        method: 'get',
        parameters: parameters,
    })
    
    
}

function getInfo(parameters, callback, container, allow_blank, format)
{
    debug_output('Get info ' + parameters);
    
    var success = function(t) {
        if (callback) {
            debug_output("Starting GetInfo callback");
            callback(t, allow_blank, container);
            debug_output("GetInfo callback completed");
        }
        
        debug_output("GetInfo " + type + " successful");
    }
    
    var failure = function(t) {
        alert("Get info " + type + " failed");
        return false;
    }
    
    if(format)
        parameters.format = format;
    
    var url = getURLParam().url_get_product_info;
    new Ajax.Request(url, {
        method:'get',
        parameters: parameters,
        onSuccess:success, 
        onFailure:failure
    });
}

function getForm(container, app_form, parameters, callback, format)
{
    var failure = function(t) {
        alert('Getting form get errors');
        return false;
    }
    
    if(!parameters)
        var parameters = {}
    
    parameters.app_form = app_form;
    parameters.format = format;
    
    url = getURLParam().url_get_form;
    new Ajax.Updater(container, url, {
        method:'get',
        parameters: parameters,
        onSuccess: callback, 
        onFailure: failure
    });
}

function updateObject(content_type, object_pk, field, value, callback)
{
    var url = new String('/ajax/update/');
    
    var success=function(t){
        if(callback) {
            callback(t);
        }
    }
    
    var failure = function() {};
    
    var parameters = {
        content_type: content_type,
        object_pk: object_pk,
        field: field,
        value: value,
    }
    
    new Ajax.Request(url, {
        method: 'post',
        parameters: parameters,
        onSuccess: success,
        onFailure: failure
    })
}

function getInfoAndUpdateObject(parameters, content_type, object_pks, field, callback)
{
    /*
    Arguments:
    parameters: Hash - Use for getInfo method
    content_type: String - use for updateObject method
    object_pk: Int/Array - use for updateObject method
    field: String - use for updateObject method
    callback: Function - use for updateObject method
    
    */
    var refresh_window = function(t) {
        var returnobj = t.responseText.evalJSON(true);
        if (returnobj.rc != 0) {
            alert(returnobj.response);
            return false;
        }
        
        window.location.reload();
    }
    
    var get_info_callback = function(t) {
        var returnobj = t.responseText.evalJSON(true);
        
        // FIXME: Display multiple items and let user to select one
        if (returnobj.length != 1) {
            alert('The item is not exist in database or mutiple instances reached.');
            return false;
        }
        
        var value = returnobj[0].pk;
        
        if (!callback)
            callback = refresh_window
        updateObject(content_type, object_pks, field, value, callback);
    }
    
    getInfo(parameters, get_info_callback);
}

// Add items to input=text as list.
// Most in use in select tag to text box.
function addItemsToTextBoxAsList(item, textbox, splitter)
{
    if(!splitter)
        var splitter = new String(',')

    if(!$F(textbox))
        $(textbox).value = item
    else
        $(textbox).value += splitter + item;
}

function getDialog(element)
{
    if(!element)
        var element = $('dialog');
        
    return element
}


var clearDialog = function(element)
{
    var dialog = getDialog(element);
    
    dialog.update(getAjaxLoading());
    dialog.hide();
}

function getAjaxLoading()
{
    return Element('div', {className: 'ajax_loading'})
}


// FIXME: Buggy here - Fuck you.
// Using in bindRefreshComponentCategoryByProduct() in testcase_actions
// Using in constructPlanComponentModificationDialog() in testplan_actions
function refreshSelectFilter(element, clean)
{
    var from = 'id_' + element + '_from';
    var to = 'id_' + element + '_to';
    
    var from_field = $(from);
    var to_field = $(to);
    
    SelectBox.cache[from] = new Array();
    SelectBox.cache[to] = new Array();
    
    if (clean) {
        to_field.update('');
        
        for (var i = 0; (node = from_field.options[i]); i++) {
            SelectBox.cache[from].push({value: node.value, text: node.text, displayed: 1});
        }
    } else {
        for (var i = 0; (node = from_field.options[i]); i++) {
            if (!node.selected)
                SelectBox.cache[from].push({value: node.value, text: node.text, displayed: 1});
        }
        
        for (var i = 0; (node = from_field.options[i]); i++) {
            if (node.selected)
                SelectBox.cache[to].push({value: node.value, text: node.text, displayed: 1});
        }
    }
}

function clickedSelectAll(checkbox, form, name)
{
    if(checkbox.checked) {
        $(form).adjacent('input[name='+ name + ']').invoke('setAttribute', 'checked', true);
    } else {
        $(form).adjacent('input[name='+ name + ']').invoke('setAttribute', 'checked', false);
        $(form).adjacent('input[name='+ name + ']').invoke('removeAttribute', 'checked');
    }
}

function bindSelectAllCheckbox(element, form, name)
{
    $(element).observe('click', function(e) {
        clickedSelectAll(this, form, name);
    })
}

function constructForm(content, action, form_observe, notice, s, c)
{
    var f = new Element('form', {'action': action});
    
    if (!s) {
        var s = new Element('input', {'type': 'submit', 'value': 'Submit'}); // Submit button
    }
    
    if (!c) {
        var c = new Element('input', {'type': 'button', 'value': 'Cancel'}); // Cancel button
        c.observe('click', function(e) {
            clearDialog();
        });
    }
    
    if(form_observe) {
        f.observe('submit', form_observe);
    }
    
    f.update(content);
    f.appendChild(s);
    f.appendChild(c);
    
    return f
}
