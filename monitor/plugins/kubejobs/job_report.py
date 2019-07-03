# Copyright (c) 2019 UFCG-LSD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class JobReport():

    def __init__(self, info_plugin, max_error=(None,None),
                 min_error=(None,None), final_replicas=None,
                 final_error=(None,None)):

        self.scaling_strategy = info_plugin['scaling_strategy']
        self.heuristic_options = info_plugin['heuristic_options']
        self.max_error = max_error
        self.min_error = min_error
        self.final_replicas = final_replicas
        self.final_error = final_error

    
    def get_max_error(self):
        return self.max_error

    def verify_and_set_max_error(self, current_error, current_time):

        if self.max_error[0] != None:
            if current_error > self.max_error[0]:
                self.max_error = (current_error, current_time)
        else:
            self.max_error = (current_error, current_time)

    def get_min_error(self):
        return self.min_error

    def verify_and_set_min_error(self, current_error, current_time):

        if self.min_error[0] != None:
            if current_error < self.min_error[0]:
                self.min_error = (current_error, current_time)
        else:
            self.min_error = (current_error, current_time)
    
    def get_final_replicas(self):
        return self.final_replicas

    def set_final_replicas(self, final_replicas):
        self.final_replicas = final_replicas

    def get_final_error(self):
        return self.final_error

    def set_final_error(self, final_error, current_time):
        self.final_error = (final_error, current_time)

    def generate_report(self, job_id):

        max_error = self.get_max_error()
        min_error = self.get_min_error()
        final_error = self.get_final_error()
        final_replicas = self.get_final_replicas()

        print max_error
        print min_error
        print final_error
        print final_replicas
        
        prefix = 'default_reports/'
        if self.scaling_strategy == 'pid':
            prefix = 'pid_reports/'
        
        f = open(prefix + job_id + "_report","w+")

        f.write("Report Job " + str(job_id) + "\n")
        f.write("Scaling Strategy: " + self.scaling_strategy + '\n\n')
        # f.write('Heuristics: ' + str(self.heuristic_options) + '\n')
        f.write("Max Error: " + str(max_error[0]) + " Timestamp: " + str(max_error[1]) + "\n")
        f.write("Min Error: " + str(min_error[0]) + " Timestamp: " + str(min_error[1]) + "\n")
        f.write("Final Error: " + str(final_error[0]) + " Timestamp: " + str(final_error[1]) + "\n")
        f.write("Final Replicas: " + str(final_replicas) + " Timestamp: " + str(final_error[1]) + "\n")
        f.write("\n\n --------- END ----------")
        
        f.close()
    

