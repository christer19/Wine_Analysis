import re
import time
import math
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

A = np.arange(0,30,1); B = np.arange(30,50,5); C = np.arange(50,250,10); D = np.arange(250,550,50)
list_target_price = np.concatenate((A,B,C,D))

price_min = 0
price_max = 100
reviews_min = 20
year_min = 2000
year_max = 2019

#Region_list = ['Corse', 'Bourgogne', 'Alsace', 'Val de Loire', 'Jura', 'Provence', 'Languedoc-Roussillon', 'Bordeaux', 'Sud-Ouest', 'Beaujolais', 'Vallée du Rhône', 'Savoie-Bugey', 'Champagne']
#Region_list = ['Bourgogne', 'Alsace', 'Val de Loire', 'Languedoc-Roussillon', 'Bordeaux', 'Vallée du Rhône']
Color_list = ['red','white','rose','sparkling']

def filter_scrapped_data(country,color):

    Country_name = convert_abbrv_fullname(country)

    rootpath = "/Users/xl332/Desktop/DataProjects/VinsFrance/data_vivino/"
    filename = 'vintage' + '_'+ color + '_'+  country + '.pkl'
    Vintage = pd.read_pickle(rootpath + filename)

    # convert non-numeric string entries to floats
    Vintage = fill_missing_values(Vintage,'Price')
    Vintage = fill_missing_values(Vintage,'Year')
    Vintage = fill_missing_values(Vintage,'ratings')
    Vintage = fill_missing_values(Vintage,'reviews')
            
    # find entries without price and remove them
    Vintage_price = Vintage.loc[Vintage['Price'] != np.nan]
    
    # find foreign entries and remove them
    Vintage_country = Vintage_price.loc[Vintage_price['Country'] == Country_name]

    # remove rows with vintage younger than 2020 and older than 1980
    Vintage_year_1 = Vintage_country.loc[Vintage_country['Year'] < 2020 ] 
    Vintage_year = Vintage_year_1.loc[Vintage_year_1['Year'] > 1980 ] 

    # clean Region name
    for index, row in Vintage_year.iterrows():
        element = row['Region']
        try:
            Region_old = Vintage_year['Region'].loc[index]
            Region_new = [character for character in Region_old if character.isalnum()]
            Region_new = "".join(Region_new)
            Region_new = Region_new.lower()
            Vintage_year['Region'].loc[index] = Region_new
        except (ValueError,TypeError,NameError):
            Vintage_year['Region'].loc[index] = np.nan

    # find duplicated entries and remove them
    Vintage_filter_index = Vintage_year.duplicated(subset=None, keep='first')
    Vintage_filter = Vintage_year[~Vintage_filter_index]

    Vintage_list = Vintage_filter

    return Vintage_list

def filter_data(Vintage_list,price_min,price_max,reviews_min,year_min,year_max):
    
    # remove rows with price exceeding threshold
    Vintage_filter1a = Vintage_list.loc[Vintage_list['Price'] <= price_max]
    Vintage_filter1 = Vintage_filter1a.loc[Vintage_filter1a['Price'] >= price_min]

    # remove rows with reviews lower than threshold
    Vintage_filter2 = Vintage_filter1.loc[Vintage_filter1['reviews'] >= reviews_min ] 

    # remove rows with vintage older than threshold 
    Vintage_filter3 = Vintage_filter2.loc[Vintage_filter2['Year'] >= year_min ] 
    Vintage_filter = Vintage_filter3.loc[Vintage_filter3['Year'] <= year_max ] 

    return Vintage_filter

    # For each region:
    # Classify wine into regions and redo 1-3 for each region
def filter_Vintage_AOC(country,color,region):

    [AOC,Region] = import_wiki_table()
    
    # determine list of AOC for each region
    index_region = np.argwhere(Region==region)
    AOC_list = AOC[index_region]
        
    Vintage = filter_scrapped_data(country,color)

    Vintage_Region = pd.DataFrame(columns = ['Country','Region','Domain','Cru','Year','ratings','reviews','link','Price'])
    n_item = 0
    for n in np.arange(0,len(AOC_list),1):
        AOC_odditem = AOC_list[n][0]
        AOC_item = [character for character in AOC_odditem if character.isalnum()]
        AOC_item = "".join(AOC_item)        
        Vintage_AOC = Vintage.loc[Vintage['Region'].str.find(AOC_item)!=-1]        
        try:
            for index, row in Vintage_AOC.iterrows():
                Vintage_Region.loc[n_item]=Vintage_AOC.loc[index]
                n_item = n_item + 1
        except (ValueError,TypeError,NameError):
            print('no data for AOC' + AOC_odditem)

    Vintage_Region_index = Vintage_Region.duplicated(subset=None, keep='first')
    Vintage_Region_ = Vintage_Region[~Vintage_Region_index]

    total_number = np.shape(Vintage)[0]
    region_number = np.shape(Vintage_Region_)[0]

    ratio = region_number / total_number * 100.0

    return Vintage_Region_, ratio

def select_by_region(country,color,region='all'):

    # Select Wine Type and Country 
    if region=='all':
        Vintage_list = filter_scrapped_data(country,color)
        ratio = 100
    else:
        [Vintage_list, ratio] = filter_Vintage_AOC(country,color,region)

    return Vintage_list, ratio

def filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max):

    Vintage_filter = filter_data(Vintage,price_min,price_max,reviews_min,year_min,year_max)

    return Vintage_filter

def fill_missing_values(Vintage,varname):

    for index, row in Vintage.iterrows():
        element = row[varname]
        try:
            Vintage[varname].loc[index] = float(element) 
        except (ValueError,TypeError,NameError): 
            Vintage[varname].loc[index] = np.nan

    return Vintage

def convert_pdframe_to_nparray(Vintage,varname):

    var_array = []
    for index, row in Vintage.iterrows():
        varval = row[varname]
        var_array.append(varval)

    var_array = np.asarray(var_array)

    return var_array

    # For all categories: 
      # 1. Graph # of item vs. price      
def get_means_bounds(var1_array,var2_array,bins_lim,alphap):

    var2_array_mean = []; var2_array_median = []
    var2_array_lower = []; var2_array_upper = []
    for n in np.arange(0, len(bins_lim)-1, 1):
        x_lower = bins_lim[n]
        x_upper = bins_lim[n+1]
        try:
            index_lower = np.argwhere(var1_array>x_lower)
            index_upper = np.argwhere(var1_array<=x_upper)
            index_cross = np.intersect1d(index_lower,index_upper)
            var2_bin = var2_array[index_cross]
            var2_mean = np.mean(var2_bin)
            var2_median = np.median(var2_bin)
            try: 
                var2_lower = np.percentile(var2_bin,alphap)
                var2_upper = np.percentile(var2_bin,100.0-alphap)
            except (ValueError,TypeError,NameError,IndexError):
                var2_lower = np.nan
                var2_upper = np.nan
        except (ValueError,TypeError,NameError,IndexError): 
            var2_mean = np.nan
            var2_median = np.nan
            var2_lower = np.nan
            var2_upper = np.nan
            
        var2_array_mean.append(var2_mean)
        var2_array_median.append(var2_median)
        var2_array_lower.append(var2_lower)
        var2_array_upper.append(var2_upper)
        
    var2_array_mean = np.asarray(var2_array_mean)
    var2_array_median = np.asarray(var2_array_median)    
    var2_array_lower = np.asarray(var2_array_lower)    
    var2_array_upper = np.asarray(var2_array_upper)    

    return var2_array_median, var2_array_mean, var2_array_upper, var2_array_lower

###############################################
# We compute the total amount of variance explained by all predictors, for each class of price range
# NB: Continuous and Categorical predictors are present

# In each price range, we compute total variance in rating, VarT
# In each price range, we compute intra-group variance in rating, VarG
# In each price range, we compute inter-group variance in rating, VarC
# amount of variance explained by predictor 1 - VarC/VarT

# produce groups by Region
def compute_explained_variance(varname,country,color):

    # price bins
    price_bins = [5, 15, 25, 35]
    
    pct_above_median_region_allprice = []; ratio_region_allprice =[]; pct_above_median_boot_lower_region_allprice = []; pct_above_median_boot_upper_region_allprice = []
    for p in np.arange(0,len(price_bins)-1,1):
        price_min = price_bins[p]
        price_max = price_bins[p+1]
        print(price_min,price_max)
        [variance_region,region_by_color_list,ratio_region,marker_list] = compute_variance_quality(varname,country,color,price_min,price_max)
        variance_region_allprice.append(variance_region)
        ratio_region_allprice.append(ratio_region)
    variance_region_allprice = np.asarray(variance_region_allprice)
    ratio_region_allprice = np.asarray(ratio_region_allprice)

#    print(pct_above_median_allprice)
    filename = 'variance_' + varname + '_' + country + '_' + color
    np.save(filename,[variance_region_allprice, region_by_color_list, ratio_region_allprice, marker_list, price_bins])

def compute_variance_quality(varname,country,color,price_min,price_max):

    region_by_color_list, marker_list = region_by_color(country,color) 
    
    # In a given price and year range,
    Vintage, ratio = select_by_region(country,color)
    Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
    var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
    var_array = var_array[~np.isnan(var_array)]
    mean_total = np.mean(var_array)
    var_array = np.subtract(var_array,mean_total)
    variance_total = np.sum(np.power(var_array,2))
    print(variance_total,mean_total,len(var_array))

    # for every region, compute number of items with ratings above median value and convert into a probability
    variance_intra_region = []; variance_inter_region = []; ratio_region = []
    for region in region_by_color_list:
        print(region)
        Vintage, ratio = select_by_region(country,color,region)
        ratio_region.append(ratio)
        Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
        var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
        var_array = var_array[~np.isnan(var_array)]
        mean_region = np.mean(var_array)
        var_array = np.subtract(var_array,mean_region)        
        variance_intra = np.sum(np.power(var_array,2))
        mean_diff = np.subtract(mean_region,mean_total)
        n_elements = len(var_array)
        variance_inter = np.power(mean_diff,2)*n_elements
        print(mean_diff,mean_diff**2,n_elements,variance_inter)
        variance_intra_region.append(variance_intra)
        variance_inter_region.append(variance_inter)

    variance_intra_region = np.asarray(variance_intra_region)
    variance_inter_region = np.asarray(variance_inter_region)
    ratio_region = np.asarray(ratio_region)

    return variance_intra_region,variance_inter_region,region_by_color_list,ratio_region,marker_list

######

# We display likelihood of wines from each region to surclass their peers, for each class of price range
def plot_probability_hist(varname,country,color):

    # load data
    filename = 'pct_above_median_' + varname + '_' + country + '_' + color
    [pct_above_median_region_allprice, pct_above_median_boot_lower_region_allprice, pct_above_median_boot_upper_region_allprice, region_by_color_list, ratio_region_allprice, marker_list, price_bins] = np.load(filename+'.npy', allow_pickle=True) 

    Country_name = convert_abbrv_fullname(country) 
    [unit,xticks,pdf_max,_] = dic_var(varname,color)

    var_array = pct_above_median_region_allprice
    var_array_lower = pct_above_median_boot_lower_region_allprice
    var_array_upper = pct_above_median_boot_upper_region_allprice
    
    bins_lim = price_bins
    nbins = np.shape(var_array)[0]
    ndata = np.shape(var_array)[1]
    bins_mean = np.add(bins_lim[:-1],bins_lim[1:])/2.0
    bins_delta = np.subtract(bins_lim[1:],bins_lim[:-1])/(ndata+1)

    bins_label = []
    for n in np.arange(0,nbins,1):
        bins_label.append(str(bins_lim[n]) + ' - ' + str(bins_lim[n+1]) ) 

    fig = plt.figure()
    for n in np.arange(0,ndata,1):
        plt.plot(bins_lim[:-1]+bins_delta*(n+1),np.squeeze(var_array[:,n]),'o'+marker_list[n], label=region_by_color_list[n])
        plt.plot(bins_lim[:-1]+bins_delta*(n+1),np.squeeze(var_array_lower[:,n]),'*'+marker_list[n])
        plt.plot(bins_lim[:-1]+bins_delta*(n+1),np.squeeze(var_array_upper[:,n]),'*'+marker_list[n])
        plt.plot([bins_lim[:-1]+bins_delta*(n+1), bins_lim[:-1]+bins_delta*(n+1)],[np.squeeze(var_array_lower[:,n]),np.squeeze(var_array_upper[:,n])],marker_list[n]+'-')

    plt.xlabel('Price range' + ' [euro]')
    plt.ylabel('[%]')
    plt.xticks(bins_mean,bins_label)
    plt.xlim(min(bins_lim),max(bins_lim))
    for m in np.arange(0,nbins+1,1):
        plt.plot([bins_lim[m], bins_lim[m]],[0, 100], 'k--', linewidth=3)
    plt.plot([bins_lim[0], bins_lim[nbins]],[50, 50], 'b--')
    plt.ylim(0,100)
    plt.legend(loc='lower left')
    title = varname + ' probability above median for ' + color + ' wine from ' + Country_name   
    savefile_name = varname + '_prob_median_' + color + '_' + country
    plt.title(title)
    fig.savefig(savefile_name+'.png')
    plt.close()

def compute_probability_hist(varname,country,color):
    
    # price bins
    price_bins = [5, 15, 25, 35]
    
    pct_above_median_region_allprice = []; ratio_region_allprice =[]; pct_above_median_boot_lower_region_allprice = []; pct_above_median_boot_upper_region_allprice = []
    for p in np.arange(0,len(price_bins)-1,1):
        price_min = price_bins[p]
        price_max = price_bins[p+1]
        print(price_min,price_max)
        pct_above_median_region,pct_above_median_boot_lower_region,pct_above_median_boot_upper_region,region_by_color_list, ratio_region, marker_list = compute_probability_quality(varname,country,color,price_min,price_max)
        pct_above_median_region_allprice.append(pct_above_median_region)
        pct_above_median_boot_lower_region_allprice.append(pct_above_median_boot_lower_region)
        pct_above_median_boot_upper_region_allprice.append(pct_above_median_boot_upper_region)
        ratio_region_allprice.append(ratio_region)
    pct_above_median_region_allprice = np.asarray(pct_above_median_region_allprice)
    pct_above_median_boot_lower_region_allprice = np.asarray(pct_above_median_boot_lower_region_allprice)
    pct_above_median_boot_upper_region_allprice = np.asarray(pct_above_median_boot_upper_region_allprice)
    ratio_region_allprice = np.asarray(ratio_region_allprice)

#    print(pct_above_median_allprice)
    filename = 'pct_above_median_' + varname + '_' + country + '_' + color
    np.save(filename,[pct_above_median_region_allprice, pct_above_median_boot_lower_region_allprice, pct_above_median_boot_upper_region_allprice, region_by_color_list, ratio_region_allprice, marker_list, price_bins])

# compute probability of quality being higher than average for each wine region for (1) price range, (2) year range 
def compute_probability_quality(varname,country,color,price_min,price_max):

    region_by_color_list, marker_list = region_by_color(country,color) 
    
    # In a given price and year range,
    Vintage, ratio = select_by_region(country,color)
    Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
    var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
    var_array = var_array[~np.isnan(var_array)]

    # the likelihood of a wine region being better than its median is:
    
    # compute median value across all regions
    var_median = np.median(var_array)
    print(var_median)

    # for every region, compute number of items with ratings above median value and convert into a probability
    pct_above_median_region = []; ratio_region = []; pct_above_median_boot_upper_region = []; pct_above_median_boot_lower_region = []
    for region in region_by_color_list:
        print(region)
        Vintage, ratio = select_by_region(country,color,region)
        ratio_region.append(ratio)
        Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
        var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
        var_array = var_array[~np.isnan(var_array)]
        var_median_region = np.median(var_array)
        len_ = len(var_array)
        len_above_median = len(var_array[np.where(var_array>=var_median)])
        pct_above_median = len_above_median/len_*100.0
        pct_above_median_region.append(pct_above_median)
        # produce bootstrap ensembles
        nbootsample = 10000; alphap = 95.0; len_above_median_boot = []
        for n in np.arange(0,nbootsample,1):
            rand_array = np.multiply(np.random.rand(len_),(len_)*np.ones(len_))
            rand_array = rand_array.astype(int)
            var_array_boot = var_array[rand_array]
            len_above_median = len(var_array_boot[np.where(var_array_boot>=var_median)])
            len_above_median_boot.append(len_above_median)
        len_above_median_boot = np.asarray(len_above_median_boot)
        len_above_median_boot_upper = np.percentile(len_above_median_boot,alphap)
        len_above_median_boot_lower = np.percentile(len_above_median_boot,100.0-alphap)
        pct_above_median_boot_upper = len_above_median_boot_upper/len_*100.0
        pct_above_median_boot_upper_region.append(pct_above_median_boot_upper)        
        pct_above_median_boot_lower = len_above_median_boot_lower/len_*100.0
        pct_above_median_boot_lower_region.append(pct_above_median_boot_lower)        

    pct_above_median_region = np.asarray(pct_above_median_region)
    pct_above_median_boot_upper_region = np.asarray(pct_above_median_boot_upper_region)
    pct_above_median_boot_lower_region = np.asarray(pct_above_median_boot_lower_region)
    ratio_region = np.asarray(ratio_region)

    return pct_above_median_region,pct_above_median_boot_lower_region,pct_above_median_boot_upper_region,region_by_color_list, ratio_region, marker_list

# 2. Graph # of reviews vs. price
# 3. Graph reviews vs. price
def get_scatter_all(varname1,varname2,country):

    for Region in Region_list:
        for color in Color_list:
            plot_scatter(varname1,varname2,country,color,Region)    

def plot_scatter(varname1,varname2,country,color,region='all'):

    Vintage, ratio = select_by_region(country,color,region)
    Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
    var1_array = convert_pdframe_to_nparray(Vintage_filter,varname1)
    var2_array = convert_pdframe_to_nparray(Vintage_filter,varname2)

    # plotting
    if region=='all':
        Country_name = convert_abbrv_fullname(country) 
    else:
        Country_name = region

    [unit1,xticks1,pdf_max,bins_lim1] = dic_var(varname1,color)
    [unit2,xticks2,pdf_max,bins_lim2] = dic_var(varname2,color)

    # compute median, mean, and envelope 
#    alphap = 66.6
    alphap = 95.0
    [median2, mean2, upper2, lower2] = get_means_bounds(var1_array,var2_array,bins_lim1,alphap)

    var1_min=min(xticks1)
    var1_max=max(xticks1)
    var2_min=min(xticks2)
    var2_max=max(xticks2)

    bins_mean1 = np.add(bins_lim1[:-1],bins_lim1[1:])/2.0
    fig = plt.figure()
    plt.plot(var1_array, var2_array, 'k*',markersize=1)
    plt.plot(bins_mean1, median2, 'm-',markersize=16)
    plt.plot(bins_mean1, mean2, 'r-',markersize=16)
    plt.plot(bins_mean1, lower2, 'b-',markersize=8)
    plt.plot(bins_mean1, upper2, 'b-',markersize=8)
    plt.xlabel(varname1+unit1)
    plt.ylabel(varname2+unit2)
    plt.xlim(var1_min,var1_max)
    plt.ylim(var2_min,var2_max)
    if varname1=='reviews':
        plt.xscale('log')
    elif varname2=='reviews':    
        plt.yscale('log')
    if region=='all':
        title = varname2 + ' vs. ' + varname1 + ' for ' +  color + ' wine from ' + Country_name   
        savefile_name = varname2 + '_vs_' +  varname1 + '_' + color + '_' + country
    else:
        title = varname2 + ' vs. ' + varname1 + ' for ' +  color + ' wine from ' + region
        savefile_name = varname2 + '_vs_' +  varname1 + '_' + color + '_' + region
    plt.title(title)
    fig.savefig(savefile_name+'.png')
    plt.close()

####
def plot_pdf_line(varname,country,color):

    region_by_color_list, marker_list = region_by_color(country,color) 

    [unit,xticks,pdf_max,bins_lim] = dic_var(varname,color)
    Country_name = convert_abbrv_fullname(country)    

    fig = plt.figure()
    n = 0
    ratio_total = 0
    for region in region_by_color_list:
        Vintage, ratio = select_by_region(country,color,region)
        Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
        var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
        var_array = var_array[~np.isnan(var_array)]
        density = stats.gaussian_kde(np.sort(var_array))
        bins_mean = np.add(bins_lim[:-1],bins_lim[1:])/2.0
        plt.plot(bins_mean, density(bins_mean), marker_list[n]+'-', linewidth=4, label=region + ' (' + str(int(ratio)) + '%) ')
        n = n + 1
        ratio_total = ratio_total + ratio 

#    plt.legend(loc='upper right')
    plt.legend(loc='upper left')
    plt.xlabel(varname+unit)
    plt.xticks(xticks)
    plt.xlim(min(bins_lim),max(bins_lim))
    plt.ylim(0,pdf_max)
    title = varname + ' PDF for ' + color + ' wine from ' + Country_name + ' (' + str(int(ratio_total)) + '%)'
    savefile_name = varname + '_density_' + color + '_' + Country_name
    plt.title(title)
    fig.savefig(savefile_name+'.png')
    plt.close()

def get_pdf_all(varname,country):

    for color in Color_list:
        plot_pdf_histogram(varname,country,color,'all')
        region_by_color_list, marker_list = region_by_color(country,color)
        for Region in region_by_color_list:
            print(color,Region)
            plot_pdf_histogram(varname,country,color,Region)

def plot_pdf_histogram(varname,country,color,region='all'):

    Vintage, ratio = select_by_region(country,color,region)
    Vintage_filter = filter_by_criteria(Vintage,price_min,price_max,reviews_min,year_min,year_max)
    var_array = convert_pdframe_to_nparray(Vintage_filter,varname)
    [unit,xticks,pdf_max,bins_lim] = dic_var(varname,color)
    Country_name = convert_abbrv_fullname(country)    
    var_array = var_array[~np.isnan(var_array)]
    density = stats.gaussian_kde(np.sort(var_array))
    bins_mean = np.add(bins_lim[:-1],bins_lim[1:])/2.0
    fig = plt.figure()
    n, x, _ = plt.hist(np.sort(var_array), density='True', edgecolor = 'black', bins = bins_lim, histtype=u'step')
    plt.plot(bins_mean, density(bins_mean), linewidth=3)
    plt.xlabel(varname+unit)
    plt.xticks(xticks)
    plt.xlim(min(bins_lim),max(bins_lim))
    plt.ylim(0,pdf_max)
    if region=='all':
        title = varname + ' PDF for ' + color + ' wine from ' + Country_name   
        savefile_name = varname + '_hist_' + color + '_' + country
    else:
        title = varname + ' PDF for ' + color + ' wine from ' + region + ' (' + str(int(ratio)) + '%)'
        savefile_name = varname + '_hist_' + color + '_' + region
    plt.title(title)
    fig.savefig(savefile_name+'.png')
    plt.close()

    # For each year: Classify wine into age group and redo 1-3 for each region
def import_wiki_table():

    url_path = 'https://fr.wikipedia.org/wiki/Vin_fran%C3%A7ais_b%C3%A9n%C3%A9ficiant_d%27une_AOC'

    data = pd.read_html(url_path)
    table = data[0]
    table = np.asarray(table)

    AOC = np.squeeze(table[:,0])
    Region = np.squeeze(table[:,1])

    # Create separate categories for duplicated name
    index_aoc = [] 
    for aoc in AOC:
        if ' ou ' in aoc:
            index = np.argwhere(aoc==AOC)
            index_aoc.append(index)
            region = Region[np.argwhere(aoc==AOC)]
            num_aoc = aoc.count(' ou ')
            aoc_split = aoc.split(' ou ')
            for n in np.arange(0,num_aoc+1,1):
                AOC = np.append(AOC,aoc_split[n])
                Region = np.append(Region,region[0][0])

    index_aoc = np.asarray(index_aoc)
    AOC_ = []; Region_ = []
    for n in np.arange(0,len(AOC),1):
        if n not in index_aoc:
            AOC_.append(AOC[n])
            Region_.append(Region[n])
    AOC_ = np.asarray(AOC_)
    Region_ = np.asarray(Region_)
            
    return AOC_, Region_
    
def dic_var(varname,color):

    if varname=='Price':
        delta = 2
        bins_lim = np.arange(0,price_max+delta,delta)
        xticks = bins_lim[0:len(bins_lim):4]
        unit = ' [euro]'
        if color=='rose':
            pdf_max = 0.1
        else:
            pdf_max = 0.05
    elif varname=='reviews':    
        delta = 10
        bins_lim = np.arange(reviews_min,2000+delta,delta)
        xticks = bins_lim[0:len(bins_lim):2] 
        pdf_max = 0.1
        unit = ''
    elif varname=='ratings':
        delta = 0.1
        bins_lim = np.arange(2.5,5+delta,delta)
        xticks = bins_lim[0:len(bins_lim):2]
        pdf_max = 2.5
        unit = ''
    elif varname=='Year':
        delta = 1
        bins_lim = np.arange(year_min,2019+delta,delta)
        xticks = bins_lim[0:len(bins_lim):2]
        pdf_max = 0.25
        unit = ''

    return unit,xticks,pdf_max,bins_lim

def convert_abbrv_fullname(country):

    if country=='FR':
        name = 'Francia'
    elif country=='IT':
        name = 'Italia'
    elif country=='ES':
        name = 'Espana'
        
    return name

def region_by_color(country,color):

    if country=='FR':
        if color=='red':
            region_by_color_list = ['Bourgogne', 'Val de Loire', 'Languedoc-Roussillon', 'Bordeaux', 'Vallée du Rhône']
            marker_list = ['b','c','m','r','g']
        elif color=='white':
            region_by_color_list = ['Bourgogne', 'Alsace', 'Val de Loire', 'Bordeaux', 'Vallée du Rhône']
            marker_list = ['b','y','m','r','g']
        elif color=='rose':
            region_by_color_list = ['Provence']
            marker_list = ['k']
        elif color=='sparkling':
            region_by_color_list = ['Champagne']
            marker_list = ['k']

    return region_by_color_list, marker_list
