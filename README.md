# Integrate-Detector-Signal
Integrate pulse-like features on a signal and estimate uncertainty in the presence of background and noise. Examples of uses include a pulse on a photodetector or PMT, ions arriving on a MCP, etc.

# Demonstration
An example of the algorithm on a generated signal, a normalized Gaussian with noise and offset. No initial guesses are given.

![image](https://user-images.githubusercontent.com/39776793/216321454-44e7b34c-e0a4-4137-b59c-bc7c86a525ec.png)

The same test is run many times on with different noise to evaluate performance

![image](https://user-images.githubusercontent.com/39776793/216321498-a36a25fb-9903-48d5-ac46-76f6ffc3520c.png)

# Notes
While a normal distribution is fitted to find the approximate location width and location of the pulse, it is not used in the integral. As such, there is no requirement that the feature be gaussian in nature. The algorithm will work as long as the feature is pulse-like and as long as no other large features are in the dataset. If your data does have other features, I recommend trimming the data fed into the code or masking out the other features before processing.
