import numpy as np
import lsst.sims.featureScheduler as fs
from lsst.sims.speedObservatory import Speed_observatory

# Run a single-filter r-band survey.
# 5-sigma depth percentile
# standard target map (WFD, NES, SCP, GP)
# Slewtime
# mask lots of off-meridian space
# No pairs
# Greedy selection of opsim fields


survey_length = 365.25*2 # days
# Define what we want the final visit ratio map to look like
target_map = fs.standard_goals()['r']

bfs = []
bfs.append(fs.Depth_percentile_basis_function())
bfs.append(fs.Target_map_basis_function(target_map=target_map))
bfs.append(fs.North_south_patch_basis_function())
bfs.append(fs.Slewtime_basis_function())

weights = np.array([.5, 1., 1., 1.])
survey = fs.Simple_greedy_survey_fields(bfs, weights, block_size=1)
scheduler = fs.Core_scheduler([survey])

observatory = Speed_observatory()
observatory, scheduler, observations = fs.sim_runner(observatory, scheduler,
                                                     survey_length=survey_length,
                                                     filename='one_filter.db',
                                                     delete_past=True)