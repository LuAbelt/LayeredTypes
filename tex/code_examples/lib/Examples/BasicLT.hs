module Examples.BasicLT where

-- Refinement type that describes a non-empty list
{-@ type NonEmpty a = {v:[a] | len v > 0 } @-}

-- Define a head function that only works on non-emtpy lists
{-@ myHead :: NonEmpty Int -> Int @-}
myHead :: [Int] -> Int
myHead (x:_) = x

{-@ ensureNonEmpty :: [Int] -> NonEmpty Int @-}
ensureNonEmpty :: [Int] -> [Int]
ensureNonEmpty [] = [0]
ensureNonEmpty x = x

i1 :: Int
-- i1 = myHead []                    -- Not allowed
i1 = myHead (ensureNonEmpty [])   -- Allowed
