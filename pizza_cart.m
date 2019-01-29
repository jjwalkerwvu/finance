% pizza_cart.m

% a small overview of costs; trying to find profit margin on each pizza_cart

% set the price; if this gets turned into a function later the price can be a
% possible input
% price in euros
pprice=7;

% let's start by keeping it simple: profit for 1 neapolitan-style pizza_cart
% prices are all in euros

% price for 125g of yeast; check this price!
p_yeast=2;
% cost of yeast for one pizza
c_yeast=p_yeast*2.5/125;

% the absurd price for organic flour, 2.29 euros for 400g.
% maybe use regular tarweel bloem which is 0.37 euros for 400g.
%p_flour=2.29;
% better price: Antimo 25 kg bag
p_flour=1.1*23;
% cost of flour for one pizza; need 567/4 =141 grams for each pizza
%c_flour=p_flour*(567/4/400);
% "Joey's Neapolitan Pizza" suggests 991 grams of flour to make 6 pizzas, each
% of which will be 10-12 inches in diameter (991/6=165 grams per pizza)
% with Antimo Caputo 25 kg bag, can make ~145 pizzas
c_flour=p_flour/145;

% the cost of basil
p_basil=1.55;
c_basil=1.55/4;

% the cost of mozzarella di bufala
c_mozzarella=2.39;
% cost of the cheaper option, regular mozzarella
c_mozzarella=0.46;

% the cost of san marzano tomatoes
p_tomatoes=1.11*50.4/24/4;
c_tomatoes=p_tomatoes;

% the cost of paper plates
% Albert Heijn sells 22 cm diameter paper plates, 20 in a package
p_pplates=0.89;
% if selling by the slice, use more plates, but profit margin goes up
c_pplates=p_pplates/20;

% the price of gas; this will be a rough estimate for now;
% figure is based on roccbox lasting 20 hrs at full blast with 5 kg of lpg 
% patio gas 
% total duration of fuel in hours
fuel_duration=20;
% approximate price for 5kg of gas:
p_gas=1.1*20.25;
% assume we operate for 2 hours; amount of money spent each day; assume we can
% cook some number of pizzas, 50? 25?
np=50;
c_gas=p_gas*(2/fuel_duration)/np;

% compute the startup cost.
su_oven=600;
% refridgerator
su_r=500;
su_tot=su_oven+su_r;

% find the total cost per pizza
c(1)=c_yeast;
c(2)=c_flour;
c(3)=c_basil;
c(4)=c_mozzarella;
c(5)=c_tomatoes;
c(6)=c_gas;
c(7)=c_pplates;
cost=sum(c);
profit=pprice-cost;
disp(strcat("Price per pizza:",num2str(pprice)));
disp(strcat("Cost per pizza:",num2str(cost)));
disp(strcat("Profit per pizza:",num2str(profit)));
disp(strcat("Startup Cost:",num2str(su_tot)));

