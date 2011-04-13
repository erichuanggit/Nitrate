function serializeProd(){
    keys = ['p_build']
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

    jQ('#btnNewProd').click(function(){
        var lastDefined = jQ('#lastDefined');
        console.log('hey');
        
    });
});
