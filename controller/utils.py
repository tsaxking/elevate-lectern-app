import netifaces
# import psutil
import numpy as np

def get_ip_address(interface: str = "eth0") -> str:
    """
    Get the IP address of a specific network interface using netifaces.

    :param interface: The name of the network interface (e.g., "eth0", "wlan0").
    :return: The IP address as a string, or None if not found.
    """
    try:
        # Get addresses for the specified interface
        addresses = netifaces.ifaddresses(interface)
        # Return the IPv4 address if available
        ipv4_info = addresses.get(netifaces.AF_INET)
        if ipv4_info and len(ipv4_info) > 0:
            return ipv4_info[0]['addr']
    except ValueError:
        pass
    return None

def remove_outliers_zscore(data, threshold=3):
    """
    Removes outliers from the data based on Z-score threshold.
    
    :param data: List of data points (numeric).
    :param threshold: Z-score threshold to define outliers (default is 3).
    :return: List of data points with outliers removed.
    """
    # Convert the data to a numpy array for easier processing
    data = np.array(data)
    
    # Calculate Z-scores
    z_scores = (data - np.mean(data)) / np.std(data)
    
    # Filter out data points with a Z-score greater than the threshold
    filtered_data = data[np.abs(z_scores) < threshold]
    
    # Return the remaining data points
    return filtered_data


# def remove_outliers_iqr(data):
#     """
#     Removes outliers from the data using the IQR method.
    
#     :param data: List of data points (numeric).
#     :return: List of data points with outliers removed.
#     """
#     # Convert the data to a numpy array for easier processing
#     data = np.array(data)
    
#     # Calculate Q1, Q3 and IQR
#     Q1 = np.percentile(data, 25)
#     Q3 = np.percentile(data, 75)
#     IQR = Q3 - Q1
    
#     # Define the lower and upper bounds for non-outliers
#     lower_bound = Q1 - 1.5 * IQR
#     upper_bound = Q3 + 1.5 * IQR
    
#     # Filter out data points outside the bounds
#     filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
    
#     # Return the remaining data points
#     return filtered_data

def remove_outliers_trim(data, trim_percent=10):
    """
    Removes the highest and lowest 'trim_percent' of data points.
    
    :param data: List of data points (numeric).
    :param trim_percent: Percent of data to trim from each end (default is 10%).
    :return: List of data points with outliers removed.
    """
    data = sorted(data)
    trim_count = int(len(data) * trim_percent / 100)
    
    # Trim the top and bottom 'trim_percent' of the data
    filtered_data = data[trim_count: -trim_count]
    
    return filtered_data

def round(num: float, sig_figs: int) -> float:
    """
    Round a number to a specified number of significant figures.

    :param num: The number to round.
    :param sig_figs: The number of significant figures to round to.
    :return: The rounded number.
    """
    return float(np.round(num, sig_figs))

def do_while(condition, action):
    """
    Perform an action repeatedly while a condition is met.

    :param condition: A function that returns a boolean value.
    :param action: A function to perform while the condition is True.
    """
    while condition():
        action()