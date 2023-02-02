def integrate_detector_signal(time:np.ndarray, signal:np.ndarray, plot:bool = True, arrival_time_guess:float = None, signal_width_guess:float = None, background_guess:float = None):
    """
    :param time:                the x-axis of the signal in arbitrary units, as a list or numpy array
    :param signal:              the y-axis of the signal in arbitrary units, as a list or numpy array
    :param plot:                a user input as to whether or not to plot the results
    :param arrival_time_guess:  a guess of the arrival time of the signal on the detector, in the same units as the "time" input
    :param signal_width_guess:  a guess of the 1-sigma width of the signal on the detector, in the same units as the "time" input
    :param background_guess:    a guess of the DC background on the detector, in the same units as the "signal" input
    :return area:               the integrated area of the signal, in units of <units of time> * <units of signal>
    :return area_SE:            the 1 sigma uncertainty estimate of the area, in units of <units of time> * <units of signal>
    """
    
    ### Define Functions ###

    def _gaussian_fit(time, signal, arrival_time_guess, signal_width_guess, background_guess):
        """
        Fits the signal to a gaussian to find its location and width
        :return fit_params:    an array containing the fitted [amplitude, width, location, background] of the signal
        :return fit_params_SE: an array containing the 1 sigma uncertanties of the fitted values
        """
        #define fit function
        def _gaussian_function(x, amplitude, sigma, location, background):
            return amplitude * np.exp(-np.square(x-location) / (2*np.square(sigma))) + background
            #amplitude not normalized so that it is easier to guess
        #if guesses are not provided, provide guesses from context
        if arrival_time_guess is None:
            arrival_time_guess = np.median(time)
        if signal_width_guess is None:
            signal_width_guess = (np.max(time) - np.min(time))/10
        if background_guess is None:
            background_guess = np.min(signal)
        amplitude_guess = np.max(signal) - np.min(signal)
        bounds = ([0, np.mean(np.diff(time)), np.min(time), -np.inf],[10*(np.max(signal) - np.min(signal)), np.max(time)-np.min(time), np.max(time), np.inf])
        #apply the fit to the data
        fit_params, cov_matrix = curve_fit(_gaussian_function, time, signal, p0 = [amplitude_guess, signal_width_guess, arrival_time_guess, background_guess], bounds = bounds)
        fit_params_SE = np.diagonal(cov_matrix)
        #return
        return fit_params, fit_params_SE

    ### Find Area ###

    #remove nan values and cast as numpy array to simplify processing
    time, signal = [np.array(array[np.logical_and(~np.isnan(time), ~np.isnan(signal))]) for array in [time, signal]]
    #fit signal to a gaussian to find location and width
    fit_params, fit_params_SE = _gaussian_fit(time, signal, arrival_time_guess, signal_width_guess, background_guess)
    signal_width, arrival_time = fit_params[1:3]
    #split signal into useful part and background. we want to integrate to 3.5 sigma, corresponding to 99.95% inclusion
    region_of_interest_indeces = np.logical_and(time>arrival_time-3.5*signal_width, time<arrival_time+3.5*signal_width)
    time_of_interest, signal_of_interest = [array[region_of_interest_indeces] for array in [time, signal]]
    time_background, signal_background = [array[~region_of_interest_indeces] for array in [time, signal]]
    #find background DC offset
    background, background_SE = np.mean(signal_background), np.std(signal_background)/np.sqrt(np.size(signal_background))
    #integrate
    area = simps(signal_of_interest-background, time_of_interest)

    ### Estimate Uncertainty ###
    
    """
    Characterize the following sources of uncertainty:
    - uncertainty in the offset
    - uncertainty from the arbitrary assignment of 3.5 sigma as integration bounds, area can change if you vary how far out you integrate
    - uncertainty from the noise on the region of interest. Since we cannot measure std(roi) background free, we rely on the points to the left of similar size
    """
    #uncertainty from background
    area_SE_background = simps(np.full(np.size(time_of_interest), background_SE), time_of_interest)
    #uncertainty from integration bounds. Go from 3.2 to 4.5 sigma and looks at how area changes
    roi_list = np.unique([np.logical_and(time>arrival_time-n_sigma*signal_width, time<arrival_time+n_sigma*signal_width) for n_sigma in np.linspace(3.2, 4.5, 100)],axis=0)
    areas_vary_nsigma = [simps(signal[roi] - background, time[roi]) for roi in roi_list]
    area_SE_n_sigma = np.std(areas_vary_nsigma)
    #uncertainty on noise in ROI:
    roi_left = np.logical_and(time<arrival_time - 3.5*signal_width, time>arrival_time - 3*3.5*signal_width)
    est_SE_ROI = np.std(signal[roi_left])
    area_SE_noiseROI = est_SE_ROI/np.sqrt(np.size(signal_of_interest))
    #add in quadrature
    area_SE = np.linalg.norm([area_SE_background, area_SE_n_sigma, area_SE_noiseROI])

    ### Plot ###

    if plot:
        plt.figure()
        plt_back = plt.scatter(time_background, signal_background)
        plt_roi = plt.scatter(time_of_interest, signal_of_interest)
        plt_fill = plt.fill_between(time_of_interest, signal_of_interest, background, alpha = 0.2, color = 'green')
        dense_times = np.linspace(np.min(time), np.max(time), 200)
        dense_gaussian = fit_params[0]*np.exp(np.divide(-np.square(dense_times - fit_params[2]), 2*fit_params[1]**2)) + fit_params[3]
        plt_fit, = plt.plot(dense_times, dense_gaussian, color = 'black')
        plt.grid()
        plt.title(f"Area = {area} ± {area_SE}")
        plt.legend([plt_back, plt_roi, plt_fit, plt_fill], ["Background", "Region of Interest", "Gaussian Fit", "Area Integrated"], prop={'size':9})
    
    ### Return ###

    return area, area_SE
    
