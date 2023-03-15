module Examples.CombinedLT where

{-@ type NonEmpty a = {v:[a] | len v > 0 } @-}
{-@ type Ordered a = [a]<{\x v -> x <= v}> @-}
-- Not possible to arbitrarly combine NonEmpty and Ordered into one refinement type
{-@ type NonEmptyOrdered a = {v:[a]<{\x v -> x >= v}> | len v > 0 }@-}

-- Extracting the maximum value from a non-empty and ordered list is equivalent to head
{-@ maxVal :: NonEmptyOrdered Int -> Int @-}
maxVal :: [Int] -> Int
maxVal (x:_) = x
