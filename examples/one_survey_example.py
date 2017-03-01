import numpy as np
import lsst.sims.featureScheduler as fs
from speed_observatory import Speed_observatory


if __name__ == "__main__":

    survey_length = 3.  # days
    # Define what we want the final visit ratio map to look like
    target_map = fs.standard_goals()['r']

    bfs = []
    bfs.append(fs.Target_map_basis_function(target_map=target_map))
    bfs.append(fs.Depth_percentile_basis_function())
    survey = fs.Simple_greedy_survey(bfs, np.array([1.]*len(bfs)))
    scheduler = fs.Core_scheduler([survey])

    observations = []
    observatory = Speed_observatory()
    mjd = observatory.mjd
    end_mjd = mjd + survey_length
    # Initiallize scheduler with conditions
    scheduler.update_conditions(observatory.return_status())

    while mjd < end_mjd:
        desired_obs = scheduler.request_observation()
        attempted_obs = observatory.attempt_observe(desired_obs)
        if attempted_obs is not None:
            scheduler.add_observation(attempted_obs)
            observations.append(attempted_obs)
        scheduler.update_conditions(observatory.return_status())
        mjd = observatory.mjd
    # Collapse observations into single array
    observations = np.array(observations)[:, 0]
    print np.size(observations)
    

