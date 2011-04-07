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
});
