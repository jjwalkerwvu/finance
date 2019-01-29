% octave_snp_500.m

% the purpose of this script is to do some basic webscraping

% read in the entire website as a character array.
% we will try to get the character symbols for all the tickers.
s=urlread('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies');

%
nyse_url='"https://www.nyse.com/quote/XNYS:';
cutoff=length(nyse_url);
indices=strfind(s,nyse_url);

ticker_urls=cell(1,length(indices));

for index=1:length(indices)
  ticker_urls{index}=s(indices(index)+cutoff:indices(index)+cutoff+4);
  % clean it up
  remove=strfind(ticker_urls{index},'"');
  if length(remove)>=1
    ticker_urls{index}(remove:end)=[];
  end
  ticker_urls{index}=strcat(s(indices(index)+1:indices(index)+cutoff-1),ticker_urls{index});
end

