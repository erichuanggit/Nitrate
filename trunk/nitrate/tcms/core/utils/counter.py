# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
# 
# Authors:
#   Xuqing Kuang <xkuang@redhat.com>

from tcms.testruns.models import TestCaseRunStatus

class CaseRunStatusCounter:
    """
    The class is use for handle count the case run with status.
    Escape the heavy work for database
    """
    def __init__(self, case_runs):
        self.case_run_status = []
        self.count_data = {}
        
        if case_runs and hasattr(case_runs, '__iter__') and hasattr(case_runs[0], 'case_run_status'):
            self.case_runs = case_runs.select_related('case_run_status')
        else:
            self.case_runs = []
        
        for tcr in TestCaseRunStatus.objects.all():
            setattr(self, tcr.name, 0)
            self.count_data[tcr.name] = 0
            self.case_run_status.append(tcr.name)
        
        self.total = len(self.case_runs)
        
        self.count()
    
    def count(self):
        """
        Count the case run numbers by case run status
        """
        for case_run in self.case_runs:
            if hasattr(case_run, 'case_run_status'):
                self.count_data[getattr(case_run.case_run_status, 'name')] = getattr(self, getattr(case_run.case_run_status, 'name')) + 1
                setattr(self, getattr(case_run.case_run_status, 'name'), getattr(self, getattr(case_run.case_run_status, 'name')) + 1)
                
        return self
    
    def complete_percent(self):
        """
        Calculate the complete percent
        """
        if not self.total:
            return 0
        
        return float(self.PASSED + self.ERROR + self.FAILED + self.WAIVED) / self.total * 100

class RunsCounter:
    def __init__(self, running = 0, finished = 0):
        self.running = running
        self.finished = finished
        self.total = running + finished
    
    def running_percent(self):
        try:
            return float(self.running) / self.total * 100
        except:
            return 0
    
    def finished_percent(self):
        try:
            return float(self.finished) / self.total * 100
        except:
            return 0

# Self testing code
if __name__ == '__main__':
    from tcms.testcases.models import TestCaseRun
    from pprint import pprint
    tcrs = TestCaseRun.objects.filter(run__run_id = 33)
    case_run_counter = CaseRunStatusCounter(tcrs)
    pprint(case_run_counter.__dict__)
