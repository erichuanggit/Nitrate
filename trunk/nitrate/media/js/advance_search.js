function serializeProd(product_id){
    var keys = ['product', 'version', 'component', 'build', 'category'];
    var hiddenArea = jQ('#hiddenArea');
    var thisProduct = jQ('<div id="prodHide'+product_id+'"></div>');
    var selectHistory = jQ('<li class="fixed clear" id="prodShow'+product_id+'"><button class="prodDel" value="'+product_id+'">Delete</button></li>');
    thisProduct.appendTo(hiddenArea);
    for(var i=0;i<keys.length;i++){
        var key = keys[i];
        var selector = jQ('#id_'+key);
        var options = selector.children('option[selected=true]');
        console.log(options);
        var texts = new Array();
        if(options!=null){
            for(var j=0;j<options.length;j++){
                var opt = options[j];
                var newInput = jQ('<input name="p_'+key+'" value="'+opt.value+'" type="hidden"/>');
                newInput.appendTo(thisProduct);
                var t = opt.text;
                if(t)
                    texts.push(t);
            }
        }
        if(texts.length>0){
            jQ('<span>'+key+': '+texts.join()+' </span>').appendTo(selectHistory);
        }
        selector.val('');
        if(key!='product')
            selector.empty();
    }
    selectHistory.appendTo(jQ('#historyArea').show());
}

jQ(function(){
    var searchForm = jQ('#frmSearch');
    var targetInp  = jQ('#inpTarget');
    jQ('#btnSearchPlan').click(function(){
        targetInp.val('plan');
        searchForm.submit();
    });
    jQ('#btnSearchCase').click(function(){
        targetInp.val('case');
        searchForm.submit();
    });
    jQ('#btnSearchRun').click(function(){
        targetInp.val('run');
        searchForm.submit();
    });

    // Refill the drop-down that is related to product
    bind_category_selector_to_product(true, true, $('id_product'), $('id_category'));
    bind_component_selector_to_product(true, true, $('id_product'), $('id_component'));
    bind_build_selector_to_product(true, $('id_product'), $('id_build'), true);
    bind_version_selector_to_product(true, true, $('id_product'), $('id_version'));

    jQ('#hiddenArea').empty();
    jQ('#historyArea').empty().hide();
    jQ('#btnNewProd').click(function(){
        var product = jQ('#id_product');
        if(product.val()){
            serializeProd(product.val());
        }else{
            return false;
        }
    });
    jQ('button.prodDel').live('click', function(){
        var pid = jQ(this).val();
        jQ('#prodHide'+pid).remove();
        jQ('#prodShow'+pid).remove();
        if(jQ('#historyArea').children().length==0){
            jQ('#historyArea').hide();
        }
    })
});
