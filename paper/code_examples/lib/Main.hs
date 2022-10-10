main :: IO ()

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

{-@ type Ordered a = [a]<{\x v -> x <= v}> @-}
-- Not possible to arbitrarly combine NonEmpty and Ordered into one refinement type
{-@ type NonEmptyOrdered a = {v:[a]<{\x v -> x >= v}> | len v > 0 }@-}

-- Extracting the maximum value from a non-empty and ordered list is equivalent to head
{-@ maxVal :: NonEmptyOrdered Int -> Int @-}
maxVal :: [Int] -> Int
maxVal (x:_) = x

main = putStrLn "Hello, Worldi!"
