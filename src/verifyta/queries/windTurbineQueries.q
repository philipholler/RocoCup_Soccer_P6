//This file was generated from (Academic) UPPAAL 4.1.20-stratego-6 (rev. 0DC1FC6317AF6369), October 2019

/*

*/
strategy safe = control: A[] not(WindTurbine.Destroyed)

/*

*/
strategy opt = maxE(power) [<=100] : <> time > 99 under safe
